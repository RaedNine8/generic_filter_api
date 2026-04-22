from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.author import Author
from app.models.book import Book
from app.models.saved_filter import SavedFilter
from tests.fixtures.factories import seed_deterministic_data


@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    db_path = Path(db_dir) / "test_filtering.sqlite"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()

    # Keep deterministic state across tests.
    session.query(Book).delete()
    session.query(Author).delete()
    session.query(SavedFilter).delete()
    session.commit()

    seed_deterministic_data(session)

    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
