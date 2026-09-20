import enum

class ExerciseErrorCode(enum.Enum):
    EXERCISE_NOT_FOUND = "Exercise not found"
    DEFAULT_EXERCISE_DELETE = "Default exercises cannot be deleted"
    DEFAULT_EXERCISE_EDIT = "Default exercises cannot be edited"