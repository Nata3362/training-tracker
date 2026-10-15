import uuid

from pydantic import BaseModel, ConfigDict

from datetime import datetime

from .models import StatusEnum


# ___Target schemas___

class TargetCreate(BaseModel):
    exercise_id: uuid.UUID
    target_weight: float
    target_reps_high: int
    target_reps_low: int


class TargetUpdate(BaseModel):
    target_weight: float|None = None
    target_reps_high: int|None = None
    target_reps_low: int|None = None


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise_id: uuid.UUID
    target_weight: float
    target_reps_high: int
    target_reps_low: int


# ___WorkoutSet schemas___

class WorkoutSetCreate(BaseModel):
    set_number: int
    performed_weight: float|None = None
    performed_reps: int|None = None


class WorkoutSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    set_number: int
    target_weight: float|None
    target_reps_high: int|None
    target_reps_low: int|None
    performed_weight: float|None
    performed_reps: int|None
    

# ___WorkoutExercise schemas___

class WorkoutExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    position: int
    sets: list[WorkoutSetCreate]

class WorkoutExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise_id: uuid.UUID
    position: int
    sets: list[WorkoutSetResponse]


# ___Workout schemas___

class WorkoutCreate(BaseModel):
    name: str
    date: datetime
    exercises: list[WorkoutExerciseCreate]

class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    date: datetime
    status: StatusEnum


class WorkoutDetail(WorkoutResponse):  
    model_config = ConfigDict(from_attributes=True)
    exercises: list[WorkoutExerciseResponse]

