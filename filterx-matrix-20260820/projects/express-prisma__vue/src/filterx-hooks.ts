export const hooks = {
  extractIdentity: (request: any) => request.header('x-genre') ?? 'Tech',
  rowPredicate: ({principal, entity}: any) => entity.name === 'Book' ? {genre: principal} : {},
  fieldVisible: ({field}: any) => field !== 'price',
};
