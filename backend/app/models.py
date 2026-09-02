from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

#Simple db model for test
#Exercise
#────────
#id
#name
class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    discipline: Mapped[str] = mapped_column(String(100))
    metric_type: Mapped[str] = mapped_column(String(50))