
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError

from .schemas import WorkoutCreate, WorkoutResponse, WorkoutDetail
from .models import Workout, WorkoutExercise, WorkoutSet
from .service import get_target_for_exercise
from ..exercise.service import get_exercise_by_id
from .error_codes import WorkoutErrorCode
from ..exercise.error_codes import ExerciseErrorCode

from ..person.models import Person
from ..person.service import get_person, get_person_optional
from ..database import get_db


router = APIRouter(prefix="/workout", tags=["workout"])
target_router = APIRouter(prefix="/target", tags=["target"])


@router.post("/new", response_model=WorkoutDetail, status_code=201)
def workout_post(
    payload: WorkoutCreate, 
    person: Person = Depends(get_person),
    db: DBSession = Depends(get_db)
) -> WorkoutDetail:
    """Save a peformed Workout with exercises and sets"""
    workout = Workout(
        name = payload.name,
        date = payload.date,
        person_id=person.id,
    )
    for exercise_in in payload.exercises:
        exercise = get_exercise_by_id(db,exercise_in.exercise_id, person.id)
        if exercise is None:
            raise HTTPException(status_code=404, detail=ExerciseErrorCode.EXERCISE_NOT_FOUND.value)
        
        workout_exercise = WorkoutExercise(
            exercise_id = exercise_in.exercise_id,
            position = exercise_in.position,
            )
        workout.exercises.append(workout_exercise)
        
        target = get_target_for_exercise(db, person.id, exercise_in.exercise_id)

        for set_in in exercise_in.sets:
            workout_set = WorkoutSet(
                set_number = set_in.set_number,
                performed_weight = set_in.performed_weight,
                performed_reps = set_in.performed_reps,
                target_weight = target.target_weight if target else None,
                target_reps_high = target.target_reps_high if target else None,
                target_reps_low = target.target_reps_low if target else None,
            )
            workout_exercise.sets.append(workout_set)
    
    db.add(workout)
    try: 
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=WorkoutErrorCode.DUPLICATE_SET_NUMBER.value)
    db.refresh(workout)

    return workout