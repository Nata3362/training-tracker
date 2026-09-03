from app.auth import verify_session
from app.models import Person, User

SIGNUP_BODY = {
    "email": "a@example.com",
    "password": "correct horse battery staple",
    "name": "A",
}


def test_signup_creates_user_and_sets_session_cookie(client):
    resp = client.post("/auth/signup", json=SIGNUP_BODY)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert "session" in resp.cookies


def test_signup_creates_linked_person_row(client, db_session):
    client.post("/auth/signup", json=SIGNUP_BODY)

    user = db_session.query(User).filter_by(email=SIGNUP_BODY["email"]).one()
    person = db_session.query(Person).filter_by(user_id=user.id).one()
    assert person.name == SIGNUP_BODY["name"]


def test_signup_duplicate_email_rejected(client):
    client.post("/auth/signup", json=SIGNUP_BODY)
    resp = client.post("/auth/signup", json=SIGNUP_BODY)

    assert resp.status_code == 409


def test_signup_does_not_store_plaintext_password(client, db_session):
    client.post("/auth/signup", json=SIGNUP_BODY)

    user = db_session.query(User).filter_by(email=SIGNUP_BODY["email"]).one()
    assert user.password_hash != SIGNUP_BODY["password"]


def test_login_with_correct_credentials_sets_new_session_cookie(client):
    client.post("/auth/signup", json=SIGNUP_BODY)

    resp = client.post(
        "/auth/login",
        json={"email": SIGNUP_BODY["email"], "password": SIGNUP_BODY["password"]},
    )

    assert resp.status_code == 200
    assert "session" in resp.cookies


def test_login_with_wrong_password_rejected(client):
    client.post("/auth/signup", json=SIGNUP_BODY)

    resp = client.post(
        "/auth/login", json={"email": SIGNUP_BODY["email"], "password": "wrong"}
    )

    assert resp.status_code == 401
    assert "session" not in resp.cookies


def test_login_with_unknown_email_rejected(client):
    resp = client.post(
        "/auth/login", json={"email": "nope@example.com", "password": "x"}
    )

    assert resp.status_code == 401


def test_logout_clears_cookie(client):
    signup = client.post("/auth/signup", json=SIGNUP_BODY)
    client.cookies.set("session", signup.cookies["session"])

    resp = client.post("/auth/logout")

    assert resp.status_code == 200
    assert resp.cookies.get("session") is None


def test_logout_revokes_the_session(client, db_session):
    signup = client.post("/auth/signup", json=SIGNUP_BODY)
    token = signup.cookies["session"]
    client.cookies.set("session", token)

    client.post("/auth/logout")

    assert verify_session(db_session, token) is None


def test_logout_without_a_session_cookie_is_a_noop(client):
    resp = client.post("/auth/logout")

    assert resp.status_code == 200
