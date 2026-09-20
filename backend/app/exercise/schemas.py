import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import EquipmentEnum, MuscleGroupEnum


class Exercise(BaseModel):
    name: str
    muscle_group: MuscleGroupEnum
    equipment: EquipmentEnum
    increment: float
    alternative1: uuid.UUID | None = None
    alternative2: uuid.UUID | None = None

class ExerciseUpdate(BaseModel):
    name: str | None = None
    muscle_group: MuscleGroupEnum | None = None
    equipment: EquipmentEnum | None = None
    increment: float | None = None
    alternative1: uuid.UUID | None = None
    alternative2: uuid.UUID | None = None

    
class ExerciseResponse(Exercise):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID | None