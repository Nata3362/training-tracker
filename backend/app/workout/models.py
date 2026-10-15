import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from ..database import Base
from enum import Enum
from sqlalchemy import Enum as SQLEnum

# _______ Enums related to workout _______
class StatusEnum(Enum):
    COMPLETED = "completed"
    INPROGRESS = "in_progress"



# _______ Tables related to workout _______
class Workout(Base):
    __tablename__ = "workout"
    name: Mapped[str] = mapped_column()
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column()
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.COMPLETED)
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.position",
    )


class Target(Base):
    __tablename__ = "target"
    __table_args__= (UniqueConstraint("person_id", "exercise_id", name="uq_person_exercise_target"),) # only one target pr. person per exercise
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise.id", ondelete="CASCADE"))
    target_weight: Mapped[float] = mapped_column()
    target_reps_high: Mapped[int] = mapped_column()
    target_reps_low: Mapped[int] = mapped_column()


class WorkoutExercise(Base):
    __tablename__ = "workout_exercise"
    workout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout.id", ondelete="CASCADE"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise.id"))
    position: Mapped[int] = mapped_column()
    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    sets: Mapped[list["WorkoutSet"]] = relationship(
        back_populates="workout_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.set_number"
    )



class WorkoutSet(Base):
    __tablename__ = "workout_set"
    __table_args__ = (UniqueConstraint("workout_exercise_id", "set_number", name="uq_workout_set_number"),)
    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_exercise.id", ondelete="CASCADE"))
    set_number: Mapped[int] = mapped_column()
    target_weight:  Mapped[float|None] = mapped_column()
    target_reps_high: Mapped[int|None] = mapped_column()
    target_reps_low: Mapped[int|None] = mapped_column()
    performed_weight: Mapped[float|None] = mapped_column()
    performed_reps: Mapped[int|None] = mapped_column()
    workout_exercise: Mapped["WorkoutExercise"] = relationship(
        back_populates="sets"
    )
