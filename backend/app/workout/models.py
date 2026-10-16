import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..database import Base
from enum import Enum
from sqlalchemy import Enum as SQLEnum

# _______ Enums related to workout _______
class StatusEnum(Enum):
    COMPLETED = "completed"
    INPROGRESS = "in_progress"



# _______ Tables related to workout _______

class WorkoutTemplate(Base):
    __tablename__= "workout_template"
    __table_args__ = (UniqueConstraint("person_id", "name", name = "uq_person_id_and_name"),)
    name: Mapped[str] = mapped_column()
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE", name="workout_template_person_id_fkey"))
    exercises: Mapped[list["ExerciseInWorkoutTemplate"]] = relationship(
        back_populates="workout_template",
        cascade="all, delete-orphan",
        order_by="ExerciseInWorkoutTemplate.position",
    )

class ExerciseInWorkoutTemplate(Base):
    __tablename__= "exercise_in_workout_template"
    __table_args__ = (UniqueConstraint("template_id", "position", name = "uq_template_id_and_position"),)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_template.id", ondelete="CASCADE", name="exercise_in_workout_template_template_id_fkey"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise.id", ondelete="CASCADE", name="exercise_in_workout_template_exercise_id_fkey"))
    position: Mapped[int] = mapped_column()
    number_of_sets: Mapped[int] = mapped_column()
    workout_template: Mapped["WorkoutTemplate"] = relationship(
            back_populates="exercises")

class Workout(Base):
    __tablename__ = "workout"
    name: Mapped[str] = mapped_column()
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE", name="workout_person_id_fkey"))
    date: Mapped[datetime] = mapped_column()
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.COMPLETED)
    template_id: Mapped[uuid.UUID|None] = mapped_column(ForeignKey("workout_template.id", ondelete="SET NULL", name="workout_template_id_fkey"))
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.position",
    )


class Target(Base):
    __tablename__ = "target"
    __table_args__= (UniqueConstraint("person_id", "exercise_id", name="uq_person_exercise_target"),) # only one target pr. person per exercise
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE", name="target_person_id_fkey"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise.id", ondelete="CASCADE", name="target_exercise_id_fkey"))
    target_weight: Mapped[float] = mapped_column()
    target_reps_high: Mapped[int] = mapped_column()
    target_reps_low: Mapped[int] = mapped_column()


class WorkoutExercise(Base):
    __tablename__ = "workout_exercise"
    __table_args__=(UniqueConstraint("workout_id", "position", name="uq_workout_id_and_position"),)
    workout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout.id", ondelete="CASCADE", name="workout_exercise_workout_id_fkey"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercise.id", name="workout_exercise_exercise_id_fkey"))
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
    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workout_exercise.id", ondelete="CASCADE", name="workout_set_workout_exercise_id_fkey"))
    set_number: Mapped[int] = mapped_column()
    target_weight:  Mapped[float|None] = mapped_column()
    target_reps_high: Mapped[int|None] = mapped_column()
    target_reps_low: Mapped[int|None] = mapped_column()
    performed_weight: Mapped[float|None] = mapped_column()
    performed_reps: Mapped[int|None] = mapped_column()
    workout_exercise: Mapped["WorkoutExercise"] = relationship(
        back_populates="sets"
    )

