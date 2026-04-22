from datetime import datetime


def author_rows() -> list[dict]:
    return [
        {
            "name": "Alice Adams",
            "email": "alice.adams@example.com",
            "country": "USA",
            "is_active": True,
            "birth_year": 1981,
            "created_at": datetime(2024, 1, 1, 10, 0, 0),
        },
        {
            "name": "Bruno Martin",
            "email": "bruno.martin@example.com",
            "country": "France",
            "is_active": False,
            "birth_year": 1975,
            "created_at": datetime(2024, 1, 2, 10, 0, 0),
        },
    ]


def book_rows(author_ids: dict[str, int]) -> list[dict]:
    return [
        {
            "title": "Alpha Filtering",
            "isbn": "9781111111111",
            "genre": "Fiction",
            "description": "A practical guide to filtering systems.",
            "price": 12.5,
            "pages": 210,
            "published_year": 2020,
            "is_available": True,
            "rating": 4.7,
            "author_id": author_ids["alice.adams@example.com"],
            "created_at": datetime(2024, 2, 1, 10, 0, 0),
        },
        {
            "title": "Beta Pagination",
            "isbn": "9782222222222",
            "genre": "Non-Fiction",
            "description": "Understanding pagination metadata and flow.",
            "price": 26.0,
            "pages": 330,
            "published_year": 2018,
            "is_available": False,
            "rating": 3.8,
            "author_id": author_ids["bruno.martin@example.com"],
            "created_at": datetime(2024, 2, 2, 10, 0, 0),
        },
        {
            "title": "Gamma Search",
            "isbn": "9783333333333",
            "genre": "Mystery",
            "description": "Search and sort edge cases in generic engines.",
            "price": 42.0,
            "pages": 500,
            "published_year": 2024,
            "is_available": True,
            "rating": 4.9,
            "author_id": author_ids["alice.adams@example.com"],
            "created_at": datetime(2024, 2, 3, 10, 0, 0),
        },
    ]
