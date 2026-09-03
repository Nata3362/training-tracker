from datetime import datetime, timedelta, timezone

from app.auth import verify_session
from app.models import AuthSession, Person, User

SIGNUP_BODY = {
    "email": "a@example.com",
    "password": "correct horse battery staple",
    "name": "A",
}

## TEST LOGIN FLOW: signup -> login -> logout
def test_signup(client, db_session):
    resp = client.post("/auth/signup", json=SIGNUP_BODY)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert "session" in resp.cookies

    user = db_session.query(User).filter_by(email=SIGNUP_BODY["email"]).one()
    person = db_session.query(Person).filter_by(user_id=user.id).one()
    assert person.name == SIGNUP_BODY["name"]

    token = resp.cookies.get("session")
    assert verify_session(db_session, token)


#TODO: hit some user endpoints with the session cookie to verify that it works, and that the user is logged in
def test_login_sets_new_session_cookie(client):
    client.post("/auth/signup", json=SIGNUP_BODY)

    old_session = client.cookies.get("session")

    resp = client.post(
        "/auth/login",
        json={"email": SIGNUP_BODY["email"], "password": SIGNUP_BODY["password"]},
    )

    assert resp.status_code == 200
    assert "session" in resp.cookies
    assert old_session != resp.cookies.get("session")


def test_logout(client, db_session):
    client.post("/auth/signup", json=SIGNUP_BODY)

    resp = client.post(
        "/auth/login", json={"email": SIGNUP_BODY["email"], "password": SIGNUP_BODY["password"]}
    )

    token = resp.cookies.get("session")

    resp = client.post("/auth/logout")

    assert resp.status_code == 200
    assert resp.cookies.get("session") is None
    assert verify_session(db_session, token) is None


def test_signup_does_not_store_plaintext_password(client, db_session):
    client.post("/auth/signup", json=SIGNUP_BODY)

    user = db_session.query(User).filter_by(email=SIGNUP_BODY["email"]).one()
    assert user.password_hash != SIGNUP_BODY["password"]


def test_logout_without_a_session_cookie_is_a_noop(client):
    resp = client.post("/auth/logout")

    assert resp.status_code == 200


# TEST ERROR CASES
def test_signup_duplicate_email_rejected(client):
    client.post("/auth/signup", json=SIGNUP_BODY)
    resp = client.post("/auth/signup", json=SIGNUP_BODY)

    assert resp.status_code == 409


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
