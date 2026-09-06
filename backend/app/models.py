from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Person(Base):
    """Auth's FK hook point. Full profile fields land with the rest of ARCHITECTURE.md's schema."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column()
