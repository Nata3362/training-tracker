from dataclasses import dataclass

from .models import EquipmentEnum, MuscleGroupEnum

@dataclass(frozen=True)
class DefaultExercise:
    name: str
    muscle_group: MuscleGroupEnum
    equipment: EquipmentEnum
    increment: float


DEFAULT_EXERCISES = [
    DefaultExercise(
        name="Bench Press",
        muscle_group= MuscleGroupEnum.CHEST,
        equipment= EquipmentEnum.BARBELL,
        increment = 1.25,
    ),

    DefaultExercise(
        name="Squat",
        muscle_group= MuscleGroupEnum.GLUTES,
        equipment= EquipmentEnum.BARBELL,
        increment = 1.25,
    ),

]