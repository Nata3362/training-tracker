import enum

class WorkoutErrorCode(enum.Enum):
    WORKOUT_NOT_FOUND = "Workout not found"
    WORKOUT_CONFLICT = "The workout could not be saved because it conflicts with existing data"