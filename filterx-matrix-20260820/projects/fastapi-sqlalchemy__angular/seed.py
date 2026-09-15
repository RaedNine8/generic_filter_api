from app.database import Base, SessionLocal, engine
from app.models.author import Author
from app.models.book import Book

Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
db = SessionLocal()
ada, bob = Author(name='Ada'), Author(name='Bob')
db.add_all([ada, bob]); db.flush()
db.add_all([Book(title='Alpha Filtering', genre='Tech', price=10, note='first', author=ada), Book(title='Beta Search', genre='Tech', price=30, note=None, author=bob), Book(title='Gamma Grouping', genre='Business', price=40, note='last', author=bob)])
db.commit(); db.close()
