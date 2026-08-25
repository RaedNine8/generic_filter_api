from fastapi import Header

def get_principal(x_genre: str = Header(default='Tech')):
    return x_genre

def row_predicate(*, principal, request, entity, model, action):
    return model.genre == principal if entity.get('model') == 'Book' else None

def field_visible(*, principal, request, entity, field, action):
    return field != 'price'
