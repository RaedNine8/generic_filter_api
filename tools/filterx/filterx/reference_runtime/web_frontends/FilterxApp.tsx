import {
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { exportEntity, groupEntity, queryEntity } from "./api";
import { FILTERX_ENTITIES } from "./entities";
import {
  cellText,
  emptyGroup,
  emptyResult,
  entityLabel,
  fieldLabel,
  initialState,
  visibleFields,
} from "./display";
import type {
  EntityConfig,
  FilterCondition,
  FilterGroup,
  FilterNode,
  FilterOperator,
  FilterxCellContext,
  FilterxContext,
  FilterxRow,
  GroupBucket,
  QueryState,
} from "./contracts";
import "./filterx.css";

export interface FilterxAppProps {
  renderHeader?: (context: FilterxContext) => ReactNode;
  renderToolbar?: (context: FilterxContext) => ReactNode;
  renderCell?: (context: FilterxCellContext) => ReactNode;
}
const OPS: FilterOperator[] = [
  "eq",
  "ne",
  "gt",
  "gte",
  "lt",
  "lte",
  "like",
  "ilike",
  "starts_with",
  "ends_with",
  "in",
  "not_in",
  "between",
  "is_null",
  "is_not_null",
];
const emptyCondition = (field = ""): FilterCondition => ({
  node_type: "condition",
  field,
  operation: "eq",
  value: "",
});

function FilterBuilder({
  entity,
  value,
  onChange,
}: {
  entity: EntityConfig;
  value: FilterGroup;
  onChange: (next: FilterGroup) => void;
}) {
  const update = (index: number, node: FilterNode) =>
    onChange({
      ...value,
      children: value.children.map((item, i) => (i === index ? node : item)),
    });
  return (
    <div className="fx-builder">
      <div className="fx-builder-head">
        <strong>Custom filters</strong>
        <select
          value={value.operator}
          onChange={(event) =>
            onChange({ ...value, operator: event.target.value as "AND" | "OR" })
          }
        >
          <option>AND</option>
          <option>OR</option>
        </select>
        <button
          onClick={() =>
            onChange({
              ...value,
              children: [
                ...value.children,
                emptyCondition(entity.fields[0]?.name),
              ],
            })
          }
        >
          + condition
        </button>
        <button
          onClick={() =>
            onChange({ ...value, children: [...value.children, emptyGroup()] })
          }
        >
          + group
        </button>
      </div>
      {value.children.map((node, index) =>
        node.node_type === "group" ? (
          <div className="fx-nested" key={index}>
            <FilterBuilder
              entity={entity}
              value={node}
              onChange={(next) => update(index, next)}
            />
          </div>
        ) : (
          <div className="fx-condition" key={index}>
            <select
              value={node.field}
              onChange={(event) =>
                update(index, { ...node, field: event.target.value })
              }
            >
              {entity.fields.map((field) => (
                <option key={field.name} value={field.name}>
                  {fieldLabel(entity, field)}
                </option>
              ))}
            </select>
            <select
              value={node.operation}
              onChange={(event) =>
                update(index, {
                  ...node,
                  operation: event.target.value as FilterOperator,
                })
              }
            >
              {OPS.map((op) => (
                <option key={op}>{op}</option>
              ))}
            </select>
            {!["is_null", "is_not_null"].includes(node.operation) && (
              <input
                value={String(node.value ?? "")}
                onChange={(event) =>
                  update(index, {
                    ...node,
                    value: ["in", "not_in", "between"].includes(node.operation)
                      ? event.target.value.split(",").map((v) => v.trim())
                      : event.target.value,
                  })
                }
              />
            )}
            <button
              aria-label="Remove filter"
              onClick={() =>
                onChange({
                  ...value,
                  children: value.children.filter((_, i) => i !== index),
                })
              }
            >
              ×
            </button>
          </div>
        ),
      )}
    </div>
  );
}

export function FilterxEntityPage({
  entity,
  renderHeader,
  renderToolbar,
  renderCell,
}: { entity: EntityConfig } & FilterxAppProps) {
  const [state, setState] = useState<QueryState>(() => initialState(entity));
  const [draft, setDraft] = useState<FilterGroup>(emptyGroup);
  const [result, setResult] = useState(emptyResult);
  const [groupField, setGroupField] = useState("");
  const [groups, setGroups] = useState<GroupBucket[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [revision, setRevision] = useState(0);
  const groupRequest = useRef(0);
  const alive = useRef(true);
  useLayoutEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      ++groupRequest.current;
    };
  }, []);
  useLayoutEffect(() => {
    let active = true;
    setError("");
    setLoading(true);
    void queryEntity<FilterxRow>(entity.route, state)
      .then((data) => {
        if (active) setResult(data);
      })
      .catch((caught) => {
        if (active) setError(String(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [entity.route, state, revision]);
  useLayoutEffect(() => {
    ++groupRequest.current;
    setGroups([]);
  }, [state, groupField, revision]);
  const visible = useMemo(
    () => visibleFields(entity, result.data),
    [entity, result.data],
  );
  const sort = (field: string) =>
    setState((old) => ({
      ...old,
      page: 1,
      sortBy: field,
      order: old.sortBy === field && old.order === "asc" ? "desc" : "asc",
    }));
  const apply = () =>
    setState((old) => ({
      ...old,
      page: 1,
      filterTree: draft.children.length ? draft : undefined,
    }));
  const group = async () => {
    if (!groupField) return;
    const request = ++groupRequest.current;
    try {
      const data = await groupEntity(
        entity.route,
        groupField,
        state.filterTree,
      );
      if (alive.current && request === groupRequest.current) setGroups(data);
    } catch (caught) {
      if (alive.current && request === groupRequest.current)
        setError(String(caught));
    }
  };
  const download = (format: "csv" | "xlsx" | "json") => {
    void exportEntity(entity.route, format, state).catch((caught) => {
      if (alive.current) setError(String(caught));
    });
  };
  const context: FilterxContext = {
    entity,
    rows: result.data,
    state,
    meta: result.meta,
    groups,
    loading,
    error,
    refresh: () => setRevision((old) => old + 1),
  };
  return (
    <main className="fx-shell">
      <header className="fx-header">
        <div>
          {renderHeader ? (
            renderHeader(context)
          ) : (
            <>
              <span className="fx-kicker">FilterX explorer</span>
              <h1>{entityLabel(entity)}</h1>
              <p>
                Filter, search, sort, group, paginate, and export live data.
              </p>
            </>
          )}
        </div>
        <div className="fx-export">
          <button onClick={() => download("csv")}>CSV</button>
          <button onClick={() => download("xlsx")}>Excel</button>
          <button onClick={() => download("json")}>JSON</button>
        </div>
      </header>
      <section className="fx-toolbar">
        <input
          aria-label="Search"
          placeholder="Search…"
          value={state.search}
          onChange={(event) =>
            setState((old) => ({ ...old, page: 1, search: event.target.value }))
          }
        />
        <select
          value={groupField}
          onChange={(event) => setGroupField(event.target.value)}
        >
          <option value="">Group by…</option>
          {entity.fields.map((field) => (
            <option key={field.name} value={field.name}>
              {fieldLabel(entity, field)}
            </option>
          ))}
        </select>
        <button disabled={!groupField} onClick={group}>
          Group
        </button>
        {renderToolbar?.(context)}
      </section>
      <FilterBuilder entity={entity} value={draft} onChange={setDraft} />
      <div className="fx-actions">
        <button className="fx-primary" onClick={apply}>
          Apply filters
        </button>
        <button
          onClick={() => {
            setDraft(emptyGroup());
            setState((old) => ({ ...old, page: 1, filterTree: undefined }));
          }}
        >
          Clear
        </button>
      </div>
      {error && <p className="fx-error">{error}</p>}
      {groups.length > 0 && (
        <section className="fx-groups">
          {groups.map((bucket, index) => (
            <article key={index}>
              <strong>{String(bucket.key ?? "Null")}</strong>
              <span>{bucket.count}</span>
            </article>
          ))}
        </section>
      )}
      <div className="fx-table-wrap">
        <table>
          <thead>
            <tr>
              {visible.map((field) => (
                <th key={field.name}>
                  <button onClick={() => sort(field.name)}>
                    {fieldLabel(entity, field)}
                    {state.sortBy === field.name
                      ? state.order === "asc"
                        ? " ↑"
                        : " ↓"
                      : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.data.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {visible.map((field) => (
                  <td key={field.name}>
                    {renderCell
                      ? renderCell({
                          ...context,
                          row,
                          rowIndex,
                          field,
                          value: row[field.name],
                        })
                      : cellText(row[field.name])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <footer className="fx-pagination">
        <span>{result.meta.total_items} results</span>
        <select
          value={state.size}
          onChange={(event) =>
            setState((old) => ({
              ...old,
              page: 1,
              size: Number(event.target.value),
            }))
          }
        >
          {[10, 20, 50, 100].map((size) => (
            <option key={size}>{size}</option>
          ))}
        </select>
        <button
          disabled={state.page <= 1}
          onClick={() => setState((old) => ({ ...old, page: old.page - 1 }))}
        >
          Previous
        </button>
        <span>
          {state.page} / {result.meta.total_pages || 1}
        </span>
        <button
          disabled={state.page >= result.meta.total_pages}
          onClick={() => setState((old) => ({ ...old, page: old.page + 1 }))}
        >
          Next
        </button>
      </footer>
    </main>
  );
}

export function FilterxApp(props: FilterxAppProps) {
  const [route, setRoute] = useState(FILTERX_ENTITIES[0]?.route ?? "");
  const entity =
    FILTERX_ENTITIES.find((item) => item.route === route) ??
    FILTERX_ENTITIES[0];
  if (!entity)
    return <p className="fx-empty">No FilterX entities were generated.</p>;
  return (
    <div className="fx-app">
      <nav className="fx-nav">
        <strong>FilterX</strong>
        {FILTERX_ENTITIES.map((item) => (
          <button
            className={item.route === entity.route ? "active" : ""}
            key={item.route}
            onClick={() => setRoute(item.route)}
          >
            {entityLabel(item)}
          </button>
        ))}
      </nav>
      <FilterxEntityPage key={entity.route} entity={entity} {...props} />
    </div>
  );
}
