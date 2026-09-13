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


# _______ Enums related to exercise _______
class MuscleGroupEnum(Enum):
    CHEST = "chest"
    BACK = "back"
    BICEPs = "biceps"
    TRICEPS = "triceps"
    GLUTES = "glutes"
    HAMSTRINGS = "hamstrings"
    CALFS = "calfs"

class EquipmentEnum(Enum):
    DUMBELL = "dumbell"
    BARBELL = "barbell"
    BODYWEIGHT = "bodyweight"
    MACHINE = "machine"

# _______ Tables related to exercise _______
class Exersice(Base):
    __tablename__ = "exercise"
    name: Mapped[str] = mapped_column()
    person_id: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("people.id"))
    muscle_group: Mapped[MuscleGroupEnum] = mapped_column(SQLEnum(MuscleGroupEnum))    
    equipment: Mapped[EquipmentEnum] = mapped_column(SQLEnum(EquipmentEnum))
    increment: Mapped[float] = mapped_column()
    alternative1: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("exercise.id"))
    alternative2: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("exercise.id"))