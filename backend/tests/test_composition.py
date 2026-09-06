from datetime import datetime, timedelta, timezone

from app.authentication.models import AuthSession

SIGNUP_BODY = {
    "email": "b@example.com",
    "password": "correct horse battery staple",
    "name": "B",
}


def test_user_returns_the_composed_identity(client):
    client.post("/auth/signup", json=SIGNUP_BODY)

    resp = client.get("/user")

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == SIGNUP_BODY["email"]
    assert body["name"] == SIGNUP_BODY["name"]


def test_user_after_logout_rejected(client):
    client.post("/auth/signup", json=SIGNUP_BODY)
    client.post("/auth/logout")

    resp = client.get("/user")

    assert resp.status_code == 401


def test_user_with_an_expired_session_rejected(client, db_session):
    client.post("/auth/signup", json=SIGNUP_BODY)

    session_row = db_session.query(AuthSession).one()
    session_row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    resp = client.get("/user")

    assert resp.status_code == 401
