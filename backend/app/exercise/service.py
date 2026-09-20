import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from .models import ExerciseModel


def get_exercise_by_id(db: DBSession, exercise_id: uuid.UUID, person_id: uuid.UUID):
    """Get an exercise by ID for a specific person"""
    return db.scalar(
        select(ExerciseModel).where(
            ExerciseModel.id == exercise_id,
            (ExerciseModel.person_id == person_id) | (ExerciseModel.person_id.is_(None))
        )
    )


def get_all_exercises(db: DBSession, person_id: uuid.UUID | None = None):
    """Get all exercises for a specific person"""
    return db.scalars(
        select(ExerciseModel).where((ExerciseModel.person_id == person_id) | (ExerciseModel.person_id.is_(None)))
    ).all()


def is_default_exercise(exercise: ExerciseModel):
    """Check if an exercise is a default exercise"""
    return exercise.person_id is None