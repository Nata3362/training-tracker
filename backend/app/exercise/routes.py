import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from .schemas import Exercise, ExerciseResponse, ExerciseUpdate
from .models import ExerciseModel
from .service import get_exercise_by_id, get_all_exercises, is_default_exercise
from .error_codes import ExerciseErrorCode

from ..person.models import Person
from ..person.service import get_person
from ..database import get_db


router = APIRouter(prefix="/exercise",tags=["exercise"])


@router.post("/new", response_model=ExerciseResponse, status_code=201)
def exercise_post(
    payload: Exercise, 
    person: Person = Depends(get_person()),
    db: DBSession = Depends(get_db)
) -> ExerciseResponse:
    """Create a new exercise"""
    exercise = ExerciseModel(
        **payload.model_dump(),
        person_id=person.id,
    )

    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    return exercise


@router.patch("/id/{exercise_id}", response_model=ExerciseResponse)
def exercise_update(
    exercise_id: uuid.UUID,
    payload: ExerciseUpdate,
    person: Person = Depends(get_person()),
    db: DBSession = Depends(get_db)
) -> ExerciseResponse:
    """Update existing exercise"""
    exercise = get_exercise_by_id(db, exercise_id, person.id)
    if exercise is None:
        raise HTTPException(status_code=404, detail=ExerciseErrorCode.EXERCISE_NOT_FOUND.value)
    if is_default_exercise(exercise):
        raise HTTPException(status_code=403, detail=ExerciseErrorCode.DEFAULT_EXERCISE_EDIT.value)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(exercise, field, value)

    db.commit()
    db.refresh(exercise)

    return exercise


@router.delete("/id/{exercise_id}", status_code=204)
def exercise_delete(
    exercise_id: uuid.UUID,
    person: Person = Depends(get_person()),
    db: DBSession = Depends(get_db)
):
    """Delete an exercise"""
    exercise = get_exercise_by_id(db, exercise_id, person.id)
    if exercise is None:
        raise HTTPException(status_code=404, detail=ExerciseErrorCode.EXERCISE_NOT_FOUND.value)
    if is_default_exercise(exercise):
        raise HTTPException(status_code=403, detail=ExerciseErrorCode.DEFAULT_EXERCISE_DELETE.value)

    db.delete(exercise)
    db.commit()


@router.get("/all", response_model=list[ExerciseResponse])
def exercise_get_all(
    person: Person | None = Depends(get_person(required=False)),
    db: DBSession = Depends(get_db)
) -> list[ExerciseResponse]:
    """Get all exercises for the current user"""
    person_id = person.id if person else None

    return get_all_exercises(db, person_id)


@router.get("/id/{exercise_id}")
def exercise_get(
    exercise_id: uuid.UUID,
    person: Person = Depends(get_person()),
    db: DBSession = Depends(get_db)
) -> ExerciseResponse:
    """Get an exercise by ID"""
    exercise = get_exercise_by_id(db, exercise_id, person.id)
    if exercise is None:
        raise HTTPException(status_code=404, detail=ExerciseErrorCode.EXERCISE_NOT_FOUND.value)

    return exercise