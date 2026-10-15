import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from .models import Target


# check if the person have a target for the requested exercise
def get_target_for_exercise(db:DBSession, person_id: uuid.UUID, exercise_id: uuid.UUID):
    return db.scalar(
        select(Target).where(
            Target.person_id == person_id,
            Target.exercise_id == exercise_id,
        )
    )