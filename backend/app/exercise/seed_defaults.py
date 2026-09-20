from sqlalchemy import select

from app.database import SessionLocal
from app.exercise.default_exercises import DEFAULT_EXERCISES
from app.exercise.models import ExerciseModel
from sqlalchemy import select

from app.database import SessionLocal
from app.exercise.default_exercises import DEFAULT_EXERCISES
from app.exercise.models import ExerciseModel
from app.person.models import Person
from app.authentication.models import User, AuthSession

def seed_default_exercises():
    with SessionLocal() as db:
        for default in DEFAULT_EXERCISES:
            existing = db.scalar(
                select(ExerciseModel).where(
                    ExerciseModel.person_id.is_(None),
                    ExerciseModel.name == default.name,
                )
            )

            if existing is None:
                db.add(
                    ExerciseModel(
                        name=default.name,
                        muscle_group=default.muscle_group,
                        equipment=default.equipment,
                        increment=default.increment,
                        person_id=None,
                    )
                )

        db.commit()


if __name__ == "__main__":
    seed_default_exercises()