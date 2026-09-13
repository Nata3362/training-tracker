"""Endpoints defined on the app itself rather than in composition."""

import pytest
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_reports_the_database(client):
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"database": True}


def test_health_fails_when_the_database_is_unreachable(client):
    # Railway routes traffic based on this endpoint, so it must not answer
    # "healthy" when the database is gone — a hardcoded reply used to.
    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_db] = broken_db

    with pytest.raises(OperationalError):
        client.get("/health")
