from enum import Enum
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from ..database import Base


# _______ Enums related to exercise _______
class MuscleGroupEnum(Enum):
    BACK = "back"
    CHEST = "chest"
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
class ExerciseModel(Base):
    __tablename__ = "exercise"
    name: Mapped[str] = mapped_column()
    person_id: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    muscle_group: Mapped[MuscleGroupEnum] = mapped_column(SQLEnum(MuscleGroupEnum))    
    equipment: Mapped[EquipmentEnum] = mapped_column(SQLEnum(EquipmentEnum))
    increment: Mapped[float] = mapped_column()
    alternative1: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("exercise.id", ondelete="SET NULL"))
    alternative2: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("exercise.id", ondelete="SET NULL"))