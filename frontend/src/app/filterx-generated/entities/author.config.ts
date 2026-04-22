import { SortOrder } from '../../core/enums/sort-order.enum';
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
} from '../../core/interfaces/entity-config.interface';

export interface Author {
  'id': number;
  'name': string;
  'email': string;
  'country': string;
  'is_active': boolean;
  'birth_year': number;
  'created_at': string;
  'updated_at': string;
}

export const AUTHOR_GENERATED_CONFIG: EntityConfig<Author> = {
  name: 'Author',
  pluralLabel: 'Authors',
  singularLabel: 'Author',
  apiEndpoint: '/api/authors',
  searchPlaceholder: 'Search author...',
  emptyMessage: 'No author records found',
  defaults: {
    pageSize: 20,
    sortField: 'id',
    sortOrder: SortOrder.ASC,
    pageSizeOptions: [10, 20, 50],
  },
  fields: [
    createFieldConfig('id', 'Id', 'number'),
    createFieldConfig('name', 'Name', 'text'),
    createFieldConfig('email', 'Email', 'text'),
    createFieldConfig('country', 'Country', 'text'),
    createFieldConfig('is_active', 'Is Active', 'boolean'),
    createFieldConfig('birth_year', 'Birth Year', 'number'),
    createFieldConfig('created_at', 'Created At', 'date'),
    createFieldConfig('updated_at', 'Updated At', 'date'),
  ],
  columns: [
    createColumnConfig<Author>('id', 'Id'),
    createColumnConfig<Author>('name', 'Name'),
    createColumnConfig<Author>('email', 'Email'),
    createColumnConfig<Author>('country', 'Country'),
    createColumnConfig<Author>('is_active', 'Is Active'),
    createColumnConfig<Author>('birth_year', 'Birth Year'),
    createColumnConfig<Author>('created_at', 'Created At'),
    createColumnConfig<Author>('updated_at', 'Updated At'),
  ],
};
