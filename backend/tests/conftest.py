import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.authentication.models import AuthSession, User
from app.person.models import Person


SIGNUP_BODY = {
    "email": "a@example.com",
    "password": "correct horse battery staple",
    "name": "A",
}

@pytest.fixture()
def create_user(client, db_session):
    """Create a user, person profile, and authenticated session for a test."""
    response = client.post("/account/signup", json=SIGNUP_BODY)

    assert response.status_code == 200

    user = db_session.query(User).filter_by(
        email=SIGNUP_BODY["email"]
    ).one()

    person = db_session.query(Person).filter_by(
        user_id=user.id
    ).one()

    session_token = client.cookies.get("session")

    auth_session = db_session.query(AuthSession).filter_by(
        user_id=user.id
    ).one()

    return {
        "client": client,
        "user": user,
        "person": person,
        "session": session_token,
        "auth_session": auth_session,
    }


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
    # SQLite ignores foreign keys unless told otherwise; turn them on so FK
    # behavior (e.g. delete restrictions) matches production Postgres.
    event.listen(eng, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
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
