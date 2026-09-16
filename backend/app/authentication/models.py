import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


"""SQLAlchemy models for users and server-side authentication sessions."""


class User(Base):
    """Account identity and password data."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class AuthSession(Base):
    """Hashed session token associated with a user and expiry time."""
    __tablename__ = "sessions"
    
    token_hash: Mapped[str] = mapped_column(unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime]
