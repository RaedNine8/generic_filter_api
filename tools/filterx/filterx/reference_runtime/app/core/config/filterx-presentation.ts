import { EntityConfig } from "../interfaces/entity-config.interface";

export interface FilterxEntityPresentation {
  label?: string;
  columns?: string[];
  labels?: Record<string, string>;
}

/** Display-only overrides. Query identifiers, permissions and defaults stay intact. */
export function applyFilterxPresentation<T>(
  config: EntityConfig<T>,
  presentation: Record<string, FilterxEntityPresentation>,
): EntityConfig<T> {
  const overrides = Object.prototype.hasOwnProperty.call(
    presentation,
    config.name,
  )
    ? presentation[config.name]
    : undefined;
  if (!overrides) return config;

  const labels = overrides.labels || {};
  const label = (name: string, fallback: string): string =>
    Object.prototype.hasOwnProperty.call(labels, name)
      ? labels[name]
      : fallback;
  // Intersect with live generated columns: removed/unknown names never become fields.
  const columns =
    overrides.columns === undefined
      ? config.columns
      : [...new Set(overrides.columns)].flatMap((name) =>
          config.columns.filter((column) => column.field === name),
        );
  return {
    ...config,
    pluralLabel: overrides.label ?? config.pluralLabel,
    fields: config.fields.map((field) => ({
      ...field,
      label: label(field.name, field.label),
    })),
    columns: columns.map((column) => ({
      ...column,
      header: label(column.field, column.header),
    })),
    groupByOptions: config.groupByOptions?.map((group) => ({
      ...group,
      label: label(group.field, group.label),
    })),
  };
}
