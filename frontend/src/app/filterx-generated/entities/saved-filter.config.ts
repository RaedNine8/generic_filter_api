import { SortOrder } from '../../core/enums/sort-order.enum';
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
} from '../../core/interfaces/entity-config.interface';

export interface SavedFilter {
  'id': number;
  'name': string;
  'description': string;
  'model_name': string;
  'filters': string;
  'filter_tree': string;
  'sort_by': string;
  'sort_order': string;
  'page_size': number;
  'search_query': string;
  'created_at': string;
  'updated_at': string;
}

export const SAVED_FILTER_GENERATED_CONFIG: EntityConfig<SavedFilter> = {
  name: 'SavedFilter',
  pluralLabel: 'SavedFilters',
  singularLabel: 'SavedFilter',
  apiEndpoint: '/api/saved-filters',
  searchPlaceholder: 'Search savedfilter...',
  emptyMessage: 'No savedfilter records found',
  defaults: {
    pageSize: 20,
    sortField: 'id',
    sortOrder: SortOrder.ASC,
    pageSizeOptions: [10, 20, 50],
  },
  fields: [
    createFieldConfig('id', 'Id', 'number'),
    createFieldConfig('name', 'Name', 'text'),
    createFieldConfig('description', 'Description', 'text'),
    createFieldConfig('model_name', 'Model Name', 'text'),
    createFieldConfig('filters', 'Filters', 'text'),
    createFieldConfig('filter_tree', 'Filter Tree', 'text'),
    createFieldConfig('sort_by', 'Sort By', 'text'),
    createFieldConfig('sort_order', 'Sort Order', 'text'),
    createFieldConfig('page_size', 'Page Size', 'number'),
    createFieldConfig('search_query', 'Search Query', 'text'),
    createFieldConfig('created_at', 'Created At', 'date'),
    createFieldConfig('updated_at', 'Updated At', 'date'),
  ],
  columns: [
    createColumnConfig<SavedFilter>('id', 'Id'),
    createColumnConfig<SavedFilter>('name', 'Name'),
    createColumnConfig<SavedFilter>('description', 'Description'),
    createColumnConfig<SavedFilter>('model_name', 'Model Name'),
    createColumnConfig<SavedFilter>('filters', 'Filters'),
    createColumnConfig<SavedFilter>('filter_tree', 'Filter Tree'),
    createColumnConfig<SavedFilter>('sort_by', 'Sort By'),
    createColumnConfig<SavedFilter>('sort_order', 'Sort Order'),
    createColumnConfig<SavedFilter>('page_size', 'Page Size'),
    createColumnConfig<SavedFilter>('search_query', 'Search Query'),
    createColumnConfig<SavedFilter>('created_at', 'Created At'),
    createColumnConfig<SavedFilter>('updated_at', 'Updated At'),
  ],
};
