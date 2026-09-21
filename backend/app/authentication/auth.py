"""Authentication services and FastAPI dependencies.

This module deals only with users, passwords, and sessions. Account
registration may call these services, but authentication does not create
person records or define account workflows.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

from ..database import get_db
from .models import AuthSession, User
from .security import hash_password, verify_password

SESSION_TTL = timedelta(days=30)


def create_user(db: DBSession, email: str, password: str) -> User:
    """Create and flush a user after checking that the email is unused."""
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()  # assigns user.id without committing yet

    return user


def authenticate_user(db: DBSession, email: str, password: str) -> User:
    """Return the matching user or raise an authentication error."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    return user


def create_session(db: DBSession, user_id: uuid.UUID) -> str:
    """Create a server-side session and return its raw cookie token."""
    # piggyback expired-row cleanup on login,
    # revisit if sessions table grows large
    db.execute(
        delete(AuthSession).where(AuthSession.expires_at <= datetime.now(timezone.utc))
    )
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.add(
        AuthSession(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + SESSION_TTL,
        )
    )
    db.flush()

    return token


def verify_session(db: DBSession, token: str) -> uuid.UUID | None:
    """Resolve a valid session token to its user ID, if it is still active."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )

    return row.user_id if row else None


def revoke_session(db: DBSession, token: str) -> None:
    """Delete the server-side session represented by a cookie token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash))
    db.commit()


def _resolve_user(session: str | None, db: DBSession) -> User | None:
    """Resolve a session cookie to its user, if the session is valid."""
    user_id = verify_session(db, session) if session is not None else None

    return db.get(User, user_id) if user_id is not None else None


def get_user(session: str | None = Cookie(default=None), db: DBSession = Depends(get_db)) -> User:
    """Resolve the session cookie to the authenticated user, or raise 401."""
    user = _resolve_user(session, db)
    if user is None:
        raise HTTPException(401, "Not authenticated")

    return user


def get_user_optional(session: str | None = Cookie(default=None), db: DBSession = Depends(get_db)) -> User | None:
    """Resolve the session cookie to the authenticated user, or None."""
    return _resolve_user(session, db)
