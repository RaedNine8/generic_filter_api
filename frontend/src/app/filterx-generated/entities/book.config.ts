import { SortOrder } from '../../core/enums/sort-order.enum';
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
} from '../../core/interfaces/entity-config.interface';

export interface Book {
  'id': number;
  'title': string;
  'isbn': string;
  'genre': string;
  'description': string;
  'price': number;
  'pages': number;
  'published_year': number;
  'is_available': boolean;
  'rating': number;
  'created_at': string;
  'updated_at': string;
  'author_id': number;
}

export const BOOK_GENERATED_CONFIG: EntityConfig<Book> = {
  name: 'Book',
  pluralLabel: 'Books',
  singularLabel: 'Book',
  apiEndpoint: '/api/books',
  searchPlaceholder: 'Search book...',
  emptyMessage: 'No book records found',
  defaults: {
    pageSize: 20,
    sortField: 'id',
    sortOrder: SortOrder.ASC,
    pageSizeOptions: [10, 20, 50],
  },
  fields: [
    createFieldConfig('id', 'Id', 'number'),
    createFieldConfig('title', 'Title', 'text'),
    createFieldConfig('isbn', 'Isbn', 'text'),
    createFieldConfig('genre', 'Genre', 'text'),
    createFieldConfig('description', 'Description', 'text'),
    createFieldConfig('price', 'Price', 'number'),
    createFieldConfig('pages', 'Pages', 'number'),
    createFieldConfig('published_year', 'Published Year', 'number'),
    createFieldConfig('is_available', 'Is Available', 'boolean'),
    createFieldConfig('rating', 'Rating', 'number'),
    createFieldConfig('created_at', 'Created At', 'date'),
    createFieldConfig('updated_at', 'Updated At', 'date'),
    createFieldConfig('author_id', 'Author Id', 'number'),
  ],
  columns: [
    createColumnConfig<Book>('id', 'Id'),
    createColumnConfig<Book>('title', 'Title'),
    createColumnConfig<Book>('isbn', 'Isbn'),
    createColumnConfig<Book>('genre', 'Genre'),
    createColumnConfig<Book>('description', 'Description'),
    createColumnConfig<Book>('price', 'Price'),
    createColumnConfig<Book>('pages', 'Pages'),
    createColumnConfig<Book>('published_year', 'Published Year'),
    createColumnConfig<Book>('is_available', 'Is Available'),
    createColumnConfig<Book>('rating', 'Rating'),
    createColumnConfig<Book>('created_at', 'Created At'),
    createColumnConfig<Book>('updated_at', 'Updated At'),
    createColumnConfig<Book>('author_id', 'Author Id'),
  ],
};
