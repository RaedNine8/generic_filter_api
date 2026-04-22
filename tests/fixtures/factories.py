from sqlalchemy.orm import Session

from app.models.author import Author
from app.models.book import Book
from tests.fixtures.datasets import author_rows, book_rows


def seed_deterministic_data(db: Session) -> None:
    authors = [Author(**row) for row in author_rows()]
    db.add_all(authors)
    db.flush()

    author_ids = {author.email: author.id for author in authors}
    books = [Book(**row) for row in book_rows(author_ids)]
    db.add_all(books)
    db.commit()
