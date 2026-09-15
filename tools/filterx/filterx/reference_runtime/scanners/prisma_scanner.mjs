import fs from "node:fs";
import path from "node:path";

const [, , schemaArgument, packageArgument] = process.argv;
if (!schemaArgument || !packageArgument) {
  console.error("Usage: prisma_scanner.mjs <schema.prisma> <package.json>");
  process.exit(2);
}

const schemaPath = path.resolve(schemaArgument);
const packagePath = path.resolve(packageArgument);
if (!fs.existsSync(schemaPath)) {
  console.error(`Prisma schema not found: ${schemaPath}`);
  process.exit(3);
}
if (!fs.existsSync(packagePath)) {
  console.error(`package.json not found: ${packagePath}`);
  process.exit(3);
}

const packageDocument = JSON.parse(fs.readFileSync(packagePath, "utf8"));
const dependencies = {
  ...(packageDocument.dependencies ?? {}),
  ...(packageDocument.devDependencies ?? {}),
};
if (!dependencies.prisma || !dependencies["@prisma/client"]) {
  console.error(
    "Prisma scanner requires both 'prisma' and '@prisma/client' in package.json. " +
      "Install them and run 'npx prisma generate' before retrying.",
  );
  process.exit(4);
}

const source = fs
  .readFileSync(schemaPath, "utf8")
  .replace(/\/\/.*$/gm, "")
  .replace(/#.*$/gm, "");

function blocks(keyword) {
  const expression = new RegExp(
    `\\b${keyword}\\s+(\\w+)\\s*\\{([\\s\\S]*?)\\}`,
    "g",
  );
  return [...source.matchAll(expression)].map((match) => ({
    name: match[1],
    body: match[2],
  }));
}

const enumValues = new Map(
  blocks("enum").map((block) => [
    block.name,
    block.body
      .split(/\r?\n/)
      .map((line) => line.trim().split(/\s+/)[0])
      .filter(Boolean),
  ]),
);
const modelBlocks = blocks("model");
const modelNames = new Set(modelBlocks.map((block) => block.name));
const scalarTypes = new Set([
  "String",
  "Int",
  "BigInt",
  "Float",
  "Decimal",
  "Boolean",
  "DateTime",
  "Json",
  "Bytes",
]);

function normalizedType(type) {
  if (type === "Int" || type === "BigInt") return "integer";
  if (type === "Float" || type === "Decimal") return "decimal";
  if (type === "Boolean") return "boolean";
  if (type === "DateTime") return "datetime";
  if (type === "Json") return "json/blob";
  if (type === "Bytes") return "binary";
  if (enumValues.has(type)) return "enum";
  return "string";
}

function operations(type) {
  if (type === "integer" || type === "decimal") {
    return [
      "eq",
      "ne",
      "gt",
      "gte",
      "lt",
      "lte",
      "in",
      "not_in",
      "between",
      "is_null",
      "is_not_null",
    ];
  }
  if (type === "boolean") return ["eq", "ne", "is_null", "is_not_null"];
  if (type === "date" || type === "datetime") {
    return [
      "eq",
      "ne",
      "gt",
      "gte",
      "lt",
      "lte",
      "between",
      "is_null",
      "is_not_null",
    ];
  }
  if (type === "json/blob" || type === "binary")
    return ["eq", "ne", "is_null", "is_not_null"];
  return [
    "eq",
    "ne",
    "like",
    "ilike",
    "starts_with",
    "ends_with",
    "in",
    "not_in",
    "is_null",
    "is_not_null",
  ];
}

function parseFields(block) {
  return block.body
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("@@"))
    .map((line) => {
      const match = line.match(/^(\w+)\s+([\w]+)(\[\])?(\?)?\s*(.*)$/);
      if (!match) return null;
      return {
        name: match[1],
        type: match[2],
        collection: Boolean(match[3]),
        nullable: Boolean(match[4]),
        attributes: match[5] ?? "",
      };
    })
    .filter(Boolean);
}

const parsedModels = new Map(
  modelBlocks.map((block) => [block.name, parseFields(block)]),
);

function tableName(block) {
  const mapped = block.body.match(/@@map\(\s*"([^"]+)"\s*\)/);
  return mapped ? mapped[1] : block.name;
}

function reverseRelationship(entityName, relationship) {
  return (parsedModels.get(relationship.type) ?? []).find(
    (candidate) =>
      candidate.type === entityName && modelNames.has(candidate.type),
  );
}

const graph = {};
for (const block of modelBlocks) {
  graph[block.name] = (parsedModels.get(block.name) ?? [])
    .filter((field) => modelNames.has(field.type))
    .map((field) => field.type)
    .sort();
}

const cycles = [];
const visiting = new Set();
const visited = new Set();
function visit(node, stack) {
  visiting.add(node);
  stack.push(node);
  for (const target of graph[node] ?? []) {
    if (visiting.has(target)) {
      const cycle = [...stack.slice(stack.indexOf(target)), target];
      if (
        !cycles.some(
          (current) => JSON.stringify(current) === JSON.stringify(cycle),
        )
      )
        cycles.push(cycle);
    } else if (!visited.has(target)) {
      visit(target, stack);
    }
  }
  stack.pop();
  visiting.delete(node);
  visited.add(node);
}
for (const node of Object.keys(graph).sort())
  if (!visited.has(node)) visit(node, []);

let maxDepth = 0;
function walkDepth(node, seen, depth) {
  maxDepth = Math.max(maxDepth, depth);
  for (const target of graph[node] ?? []) {
    if (!seen.has(target))
      walkDepth(target, new Set([...seen, target]), depth + 1);
  }
}
for (const node of Object.keys(graph)) walkDepth(node, new Set([node]), 0);

const entities = modelBlocks
  .map((block) => {
    const parsed = parsedModels.get(block.name) ?? [];
    const fields = parsed
      .filter(
        (field) => scalarTypes.has(field.type) || enumValues.has(field.type),
      )
      .map((field) => {
        const category = normalizedType(field.type);
        const foreignKeys = [];
        for (const relation of parsed.filter((candidate) =>
          modelNames.has(candidate.type),
        )) {
          const relationFields = relation.attributes
            .match(/fields\s*:\s*\[([^\]]+)\]/)?.[1]
            ?.split(",")
            .map((item) => item.trim());
          const references = relation.attributes
            .match(/references\s*:\s*\[([^\]]+)\]/)?.[1]
            ?.split(",")
            .map((item) => item.trim());
          const index = relationFields?.indexOf(field.name) ?? -1;
          if (index >= 0)
            foreignKeys.push(`${relation.type}.${references?.[index] ?? "id"}`);
        }
        return {
          name: field.name,
          type: category,
          source_type: field.type,
          nullable: field.nullable,
          primary_key: /@id\b/.test(field.attributes),
          unique: /@unique\b/.test(field.attributes),
          has_default: /@default\s*\(/.test(field.attributes),
          foreign_keys: foreignKeys.sort(),
          operations: operations(category),
          enum_values: enumValues.get(field.type) ?? [],
          visibility: "public",
          permission: null,
        };
      });
    const relationships = parsed
      .filter((field) => modelNames.has(field.type))
      .map((field) => {
        const reverse = reverseRelationship(block.name, field);
        let kind;
        if (field.collection && reverse?.collection) kind = "many-to-many";
        else if (field.collection) kind = "one-to-many";
        else if (reverse?.collection) kind = "many-to-one";
        else kind = "one-to-one";
        return {
          name: field.name,
          kind,
          target_entity: field.type,
          target_table: tableName(
            modelBlocks.find((candidate) => candidate.name === field.type),
          ),
          join_path: [field.name],
          depth: 1,
          collection: field.collection,
          back_populates: reverse?.name ?? null,
          cycle: cycles.some(
            (cycle) => cycle.includes(block.name) && cycle.includes(field.type),
          ),
        };
      })
      .sort((left, right) => left.name.localeCompare(right.name));
    const softDeleteField = fields.find((field) =>
      ["deletedAt", "deleted_at", "isDeleted", "is_deleted"].includes(
        field.name,
      ),
    );
    return {
      name: block.name,
      identity: {
        module: "prisma",
        table: tableName(block),
        primary_keys: fields
          .filter((field) => field.primary_key)
          .map((field) => field.name),
      },
      fields,
      relationships,
      cycle_memberships: cycles.filter((cycle) => cycle.includes(block.name)),
      soft_delete: {
        respected: Boolean(softDeleteField),
        field: softDeleteField?.name ?? null,
      },
    };
  })
  .sort((left, right) => left.name.localeCompare(right.name));

process.stdout.write(
  JSON.stringify({
    version: "filterx-ir/v1",
    source_framework: "prisma",
    entities,
    routes: [],
    security: {
      identity: null,
      row_predicates: [],
      entity_row_predicates: [],
      field_visibility: null,
    },
    max_relationship_depth: maxDepth,
  }),
);
