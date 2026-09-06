import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

from ..database import get_db
from .models import AuthSession, User
from .security import hash_password, verify_password

SESSION_TTL = timedelta(days=30)


def create_user(db: DBSession, email: str, password: str) -> User:
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()  # assigns user.id without committing yet
    return user


def authenticate_user(db: DBSession, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return user


def create_session(db: DBSession, user_id: int) -> str:
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
    db.commit()
    return token


def verify_session(db: DBSession, token: str) -> int | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )
    return row.user_id if row else None


def revoke_session(db: DBSession, token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash))
    db.commit()


async def require_auth(
    # dependency for routes that need a logged-in user, e.g.
    # user_id: int = Depends(require_auth)
    session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> int:
    if session is None:
        raise HTTPException(401, "Not logged in")
    user_id = verify_session(db, session)
    if user_id is None:
        raise HTTPException(401, "Session expired or invalid")
    return user_id
