import uuid

from fastapi import APIRouter, HTTPException, Cookie, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from ..authentication.auth import (
    require_auth,
    get_user,
)
from ..authentication.models import User
from .schemas import Exercise, ExerciseResponse, ExerciseUpdate
from ..database import get_db
from app.exercise.models import ExerciseModel
from ..person.models import Person

router = APIRouter(prefix="/exercise",tags=["exercise"])


@router.post("/new", response_model=ExerciseResponse, status_code=201)
def exercise_post(
    payload: Exercise, 
    user_id: uuid.UUID = Depends(require_auth),
    db: DBSession = Depends(get_db)
):
    """Create a new exercise"""
    person = db.scalar(
        select(Person).where(Person.user_id == user_id)
    )
    
    exercise = ExerciseModel(
        **payload.model_dump(),
        person_id = person.id,
    )

    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    return exercise


@router.patch("/update/{exercise_id}", response_model=ExerciseResponse)
def exercise_update(
    exercise_id: uuid.UUID,
    payload: ExerciseUpdate,
    user_id: uuid.UUID = Depends(require_auth),
    db: DBSession = Depends(get_db)
):
    """Update existing exersice"""
    person = db.scalar(select(Person).where(Person.user_id == user_id)) 

    exercise = db.scalar(
        select(ExerciseModel).where(
            ExerciseModel.id == exercise_id, 
            ExerciseModel.person_id == person.id
        )
    )
    if exercise is None:
        raise HTTPException(status_code=404, detail="Execise not found")
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(exercise, field, value)

    db.commit()
    db.refresh(exercise)

    return exercise   



@router.put("/exercise/{id}")
def exercise_put(
    payload: Exercise, 
    response: ExerciseResponse,
    user_id = Depends(require_auth),
    DBSession = Depends(get_db)
):
    pass


@router.get("/exercise/{id}")
def exercise_get(
    payload: Exercise, 
    response: ExerciseResponse,
    user_id = Depends(get_user),
    DBSession = Depends(get_db)
):
    pass


@router.delete("/exercise/{id}")
def exercise_delete(
    response: ExerciseResponse,
    user_id = Depends(require_auth),
    DBSession = Depends(get_db)
):
    pass
