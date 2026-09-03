import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def engine():
    # in-memory sqlite db only exists on the connection that created it, so
    # StaticPool reuses a single connection for the whole engine (else each
    # checkout would see a separate, tableless db); check_same_thread=False
    # allows that one connection to be used from TestClient's request thread.
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)  # fresh schema per test
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    # direct ORM session for tests that want to seed/assert against the db
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # route the app's db dependency to the test engine instead of the real db
    app.dependency_overrides[get_db] = override_get_db
    # https base_url so Secure cookies (set on session cookies) get sent back
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()
