from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
import uuid
from sqlalchemy import Enum as SQLEnum
from .database import Base

# ______ Tables related to person _______

class Person(Base):
    """Auth's FK hook point. Full profile fields land with the rest of ARCHITECTURE.md's schema."""

    __tablename__ = "people"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column()



