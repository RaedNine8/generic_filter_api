<script setup lang="ts">
import type {
  EntityConfig,
  FilterCondition,
  FilterGroup,
  FilterNode,
  FilterOperator,
} from "./contracts";
import { emptyGroup, fieldLabel } from "./display";
const props = defineProps<{ entity: EntityConfig; modelValue: FilterGroup }>();
const emit = defineEmits<{
  (event: "update:modelValue", value: FilterGroup): void;
}>();
const operations: FilterOperator[] = [
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
function changed(children: FilterNode[]) {
  emit("update:modelValue", { ...props.modelValue, children });
}
function update(index: number, node: FilterNode) {
  changed(
    props.modelValue.children.map((item, i) => (i === index ? node : item)),
  );
}
function condition(): FilterCondition {
  return {
    node_type: "condition",
    field: props.entity.fields[0]?.name ?? "",
    operation: "eq",
    value: "",
  };
}
function inputValue(event: Event, operation: FilterOperator): unknown {
  const value = (event.target as HTMLInputElement).value;
  return ["in", "not_in", "between"].includes(operation)
    ? value.split(",").map((item) => item.trim())
    : value;
}
</script>
<template>
  <section class="fx-builder">
    <div class="fx-builder-head">
      <strong>Custom filters</strong
      ><select
        :value="modelValue.operator"
        @change="
          emit('update:modelValue', {
            ...modelValue,
            operator: ($event.target as HTMLSelectElement).value as
              | 'AND'
              | 'OR',
          })
        "
      >
        <option>AND</option>
        <option>OR</option></select
      ><button @click="changed([...modelValue.children, condition()])">
        + condition</button
      ><button @click="changed([...modelValue.children, emptyGroup()])">
        + group
      </button>
    </div>
    <template v-for="(node, index) in modelValue.children" :key="index">
      <FilterxFilterBuilder
        v-if="node.node_type === 'group'"
        class="fx-nested"
        :entity="entity"
        :model-value="node"
        @update:model-value="(next: FilterGroup) => update(index, next)"
      />
      <div v-else class="fx-condition">
        <select
          :value="node.field"
          @change="
            update(index, {
              ...node,
              field: ($event.target as HTMLSelectElement).value,
            })
          "
        >
          <option
            v-for="field in entity.fields"
            :key="field.name"
            :value="field.name"
          >
            {{ fieldLabel(entity, field) }}
          </option>
        </select>
        <select
          :value="node.operation"
          @change="
            update(index, {
              ...node,
              operation: ($event.target as HTMLSelectElement)
                .value as FilterOperator,
            })
          "
        >
          <option v-for="op in operations" :key="op">{{ op }}</option>
        </select>
        <input
          v-if="!['is_null', 'is_not_null'].includes(node.operation)"
          :value="String(node.value ?? '')"
          @input="
            update(index, {
              ...node,
              value: inputValue($event, node.operation),
            })
          "
        />
        <button
          aria-label="Remove filter"
          @click="changed(modelValue.children.filter((_, i) => i !== index))"
        >
          ×
        </button>
      </div>
    </template>
  </section>
</template>
