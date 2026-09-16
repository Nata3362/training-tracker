"""SQLAlchemy model for the person profile linked to a user account."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from ..database import Base

# ______ Tables related to person _______

class Person(Base):
    """Profile data owned by one authenticated user."""

    __tablename__ = "people"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column()