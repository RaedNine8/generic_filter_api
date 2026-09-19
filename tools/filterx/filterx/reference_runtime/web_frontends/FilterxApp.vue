<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
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
import FilterxFilterBuilder from "./FilterxFilterBuilder.vue";
import type {
  FilterxCellContext,
  FilterxContext,
  FilterxRow,
  GroupBucket,
} from "./contracts";
import "./filterx.css";

defineSlots<{
  header?(props: FilterxContext): unknown;
  toolbar?(props: FilterxContext): unknown;
  cell?(props: FilterxCellContext): unknown;
}>();
const route = ref(FILTERX_ENTITIES[0]?.route ?? "");
const entity = computed(
  () =>
    FILTERX_ENTITIES.find((item) => item.route === route.value) ??
    FILTERX_ENTITIES[0],
);
const state = ref(initialState(entity.value));
const filters = ref(emptyGroup());
const result = ref(emptyResult());
const groupField = ref("");
const groups = ref<GroupBucket[]>([]);
const error = ref("");
const loading = ref(false);
let alive = true;
let requestId = 0;
let groupRequestId = 0;
const visible = computed(() =>
  entity.value ? visibleFields(entity.value, result.value.data) : [],
);
async function load() {
  const request = ++requestId;
  ++groupRequestId;
  groups.value = [];
  if (!entity.value) return;
  error.value = "";
  loading.value = true;
  try {
    const data = await queryEntity<FilterxRow>(entity.value.route, state.value);
    if (alive && request === requestId) result.value = data;
  } catch (caught) {
    if (alive && request === requestId) error.value = String(caught);
  } finally {
    if (alive && request === requestId) loading.value = false;
  }
}
// Invalidate old promises synchronously, before the next entity can be displayed.
watch(
  () => entity.value?.route,
  () => {
    ++requestId;
    ++groupRequestId;
    filters.value = emptyGroup();
    result.value = emptyResult();
    groupField.value = "";
    groups.value = [];
    error.value = "";
    loading.value = false;
    state.value = initialState(entity.value);
  },
  { flush: "sync" },
);
watch(
  state,
  () => {
    ++requestId;
    ++groupRequestId;
    groups.value = [];
  },
  { deep: true, flush: "sync" },
);
watch(
  groupField,
  () => {
    ++groupRequestId;
    groups.value = [];
  },
  { flush: "sync" },
);
watch(
  state,
  () => {
    void load();
  },
  { deep: true, immediate: true },
);
onBeforeUnmount(() => {
  alive = false;
  ++requestId;
  ++groupRequestId;
});
function sort(field: string) {
  state.value = {
    ...state.value,
    page: 1,
    sortBy: field,
    order:
      state.value.sortBy === field && state.value.order === "asc"
        ? "desc"
        : "asc",
  };
}
function apply() {
  state.value = {
    ...state.value,
    page: 1,
    filterTree: filters.value.children.length
      ? JSON.parse(JSON.stringify(filters.value))
      : undefined,
  };
}
function clear() {
  filters.value = emptyGroup();
  state.value = { ...state.value, page: 1, filterTree: undefined };
}
async function group() {
  if (!entity.value || !groupField.value) return;
  const request = ++groupRequestId;
  try {
    const data = await groupEntity(
      entity.value.route,
      groupField.value,
      state.value.filterTree,
    );
    if (alive && request === groupRequestId) groups.value = data;
  } catch (caught) {
    if (alive && request === groupRequestId) error.value = String(caught);
  }
}
async function download(format: "csv" | "xlsx" | "json") {
  if (!entity.value) return;
  const currentRoute = entity.value.route;
  try {
    await exportEntity(currentRoute, format, state.value);
  } catch (caught) {
    if (alive && currentRoute === entity.value?.route)
      error.value = String(caught);
  }
}
const context = computed<FilterxContext | undefined>(() =>
  entity.value
    ? {
        entity: entity.value,
        rows: result.value.data,
        state: state.value,
        meta: result.value.meta,
        groups: groups.value,
        loading: loading.value,
        error: error.value,
        refresh: () => {
          void load();
        },
      }
    : undefined,
);
</script>
<template>
  <div v-if="entity && context" class="fx-app">
    <nav class="fx-nav">
      <strong>FilterX</strong
      ><button
        v-for="item in FILTERX_ENTITIES"
        :key="item.route"
        :class="{ active: item.route === entity.route }"
        @click="route = item.route"
      >
        {{ entityLabel(item) }}
      </button>
    </nav>
    <main :key="entity.route" class="fx-shell">
      <header class="fx-header">
        <div>
          <slot name="header" v-bind="context"
            ><span class="fx-kicker">FilterX explorer</span>
            <h1>{{ entityLabel(entity) }}</h1>
            <p>
              Filter, search, sort, group, paginate, and export live data.
            </p></slot
          >
        </div>
        <div class="fx-export">
          <button
            v-for="format in ['csv', 'xlsx', 'json'] as const"
            :key="format"
            @click="download(format)"
          >
            {{ format.toUpperCase() }}
          </button>
        </div>
      </header>
      <section class="fx-toolbar">
        <input
          :value="state.search"
          aria-label="Search"
          placeholder="Search…"
          @input="
            state = {
              ...state,
              page: 1,
              search: ($event.target as HTMLInputElement).value,
            }
          "
        /><select v-model="groupField">
          <option value="">Group by…</option>
          <option
            v-for="field in entity.fields"
            :key="field.name"
            :value="field.name"
          >
            {{ fieldLabel(entity, field) }}
          </option></select
        ><button :disabled="!groupField" @click="group">Group</button
        ><slot name="toolbar" v-bind="context" />
      </section>
      <FilterxFilterBuilder v-model="filters" :entity="entity" />
      <div class="fx-actions">
        <button class="fx-primary" @click="apply">Apply filters</button
        ><button @click="clear">Clear</button>
      </div>
      <p v-if="error" class="fx-error">{{ error }}</p>
      <section v-if="groups.length" class="fx-groups">
        <article v-for="(bucket, index) in groups" :key="index">
          <strong>{{ String(bucket.key ?? "Null") }}</strong
          ><span>{{ bucket.count }}</span>
        </article>
      </section>
      <div class="fx-table-wrap">
        <table>
          <thead>
            <tr>
              <th v-for="field in visible" :key="field.name">
                <button @click="sort(field.name)">
                  {{ fieldLabel(entity, field)
                  }}{{
                    state.sortBy === field.name
                      ? state.order === "asc"
                        ? " ↑"
                        : " ↓"
                      : ""
                  }}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in result.data" :key="rowIndex">
              <td v-for="field in visible" :key="field.name">
                <slot
                  name="cell"
                  v-bind="context"
                  :row="row"
                  :row-index="rowIndex"
                  :field="field"
                  :value="row[field.name]"
                  >{{ cellText(row[field.name]) }}</slot
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <footer class="fx-pagination">
        <span>{{ result.meta.total_items }} results</span
        ><select
          :value="state.size"
          @change="
            state = {
              ...state,
              page: 1,
              size: Number(($event.target as HTMLSelectElement).value),
            }
          "
        >
          <option v-for="size in [10, 20, 50, 100]" :key="size">
            {{ size }}
          </option></select
        ><button :disabled="state.page <= 1" @click="state.page--">
          Previous</button
        ><span>{{ state.page }} / {{ result.meta.total_pages || 1 }}</span
        ><button
          :disabled="state.page >= result.meta.total_pages"
          @click="state.page++"
        >
          Next
        </button>
      </footer>
    </main>
  </div>
  <p v-else class="fx-empty">No FilterX entities were generated.</p>
</template>
