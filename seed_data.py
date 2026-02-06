import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.author import Author
from app.models.book import Book


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def seed_data():
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Author).count() > 0:
            print("Data already exists. Skipping seed.")
            return
        
        # Sample data
        countries = ["USA", "UK", "France", "Germany", "Japan", "Canada", "Australia", "Spain", "Italy", "Brazil"]
        genres = ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", "Romance", "Horror", "Biography"]
        
        authors_data = [
            {"name": "John Smith", "email": "john.smith@email.com", "country": "USA", "birth_year": 1975},
            {"name": "Jane Doe", "email": "jane.doe@email.com", "country": "UK", "birth_year": 1982},
            {"name": "Pierre Martin", "email": "pierre.martin@email.com", "country": "France", "birth_year": 1968},
            {"name": "Hans Mueller", "email": "hans.mueller@email.com", "country": "Germany", "birth_year": 1990},
            {"name": "Yuki Tanaka", "email": "yuki.tanaka@email.com", "country": "Japan", "birth_year": 1985},
            {"name": "Maria Garcia", "email": "maria.garcia@email.com", "country": "Spain", "birth_year": 1978},
            {"name": "Lucas Silva", "email": "lucas.silva@email.com", "country": "Brazil", "birth_year": 1992},
            {"name": "Emma Wilson", "email": "emma.wilson@email.com", "country": "Canada", "birth_year": 1970},
            {"name": "Marco Rossi", "email": "marco.rossi@email.com", "country": "Italy", "birth_year": 1965},
            {"name": "Sarah Johnson", "email": "sarah.johnson@email.com", "country": "Australia", "birth_year": 1988},
            {"name": "Robert Brown", "email": "robert.brown@email.com", "country": "USA", "birth_year": 1955},
            {"name": "Alice Wang", "email": "alice.wang@email.com", "country": "USA", "birth_year": 1995},
        ]
        
        # Create authors
        authors = []
        for data in authors_data:
            author = Author(
                name=data["name"],
                email=data["email"],
                country=data["country"],
                birth_year=data["birth_year"],
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            db.add(author)
            authors.append(author)
        
        db.flush()  # Get IDs
        print(f"Created {len(authors)} authors")
        
        # Book titles
        book_titles = [
            "The Silent Echo", "Midnight Dreams", "Beyond the Horizon", "The Last Kingdom",
            "Shadows of Tomorrow", "The Crystal Heart", "Echoes of Eternity", "The Hidden Path",
            "Whispers in the Dark", "The Golden Gate", "Storm Rising", "The Forgotten Realm",
            "Dancing with Destiny", "The Iron Crown", "Secrets of the Deep", "The Wanderer's Tale",
            "Flames of Passion", "The Silver Moon", "Lost in Time", "The Dark Tower",
            "Ocean's Promise", "The Phoenix Rising", "Winter's End", "The Jade Dragon",
            "Mystery of the Manor", "The Starlight Express", "Beneath the Surface", "The Royal Guard",
            "Dreams of Glory", "The Secret Garden", "Thunder Valley", "The Emerald City",
            "Hearts Aflame", "The Crimson Sky", "Journey to Nowhere", "The Glass Castle",
            "Winds of Change", "The Diamond Throne", "Sunrise Boulevard", "The Mystic River",
            "Love in Paris", "The Ancient Scrolls", "Night's Edge", "The Brave Knight",
            "Tides of Fortune", "The Enchanted Forest", "Desert Storm", "The Silent Witness"
        ]
        
        # Create books
        books_created = 0
        for i, title in enumerate(book_titles):
            author = random.choice(authors)
            book = Book(
                title=title,
                isbn=f"978-{random.randint(1000000000, 9999999999)}",
                genre=random.choice(genres),
                description=f"An exciting {random.choice(genres).lower()} book about {title.lower()}.",
                price=round(random.uniform(9.99, 59.99), 2),
                pages=random.randint(150, 800),
                published_year=random.randint(1990, 2025),
                is_available=random.choice([True, True, True, False]),  # 75% available
                rating=round(random.uniform(2.5, 5.0), 1),
                author_id=author.id
            )
            db.add(book)
            books_created += 1
        
        db.commit()
        print(f"Created {books_created} books")
        print("Seed data created successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating tables...")
    create_tables()
    print("Seeding data...")
    seed_data()
    print("Done!")
