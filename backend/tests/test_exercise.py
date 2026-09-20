import uuid
import pytest
from sqlalchemy import select

from app.authentication.models import User
from app.exercise.models import EquipmentEnum, ExerciseModel, MuscleGroupEnum
from app.exercise.error_codes import ExerciseErrorCode
from app.person.models import Person


EXERCISE_BODY = {
        "name": "Bench Press",
        "muscle_group": "chest",
        "equipment": "barbell",
        "increment": 2.5,
        "alternative1": None,
        "alternative2": None,
}


@pytest.fixture
def setup_exercises(create_user, db_session):
    """Setup the database with an owned, a default, and someone else's exercise."""
    person = create_user["person"]

    other_user = User(email="other@example.com", password_hash="x")
    db_session.add(other_user)
    db_session.flush()
    other_person = Person(user_id=other_user.id, name="Other")
    db_session.add(other_person)
    db_session.flush()

    exercises = {
        "own": ExerciseModel(
            name="Squat", muscle_group=MuscleGroupEnum.GLUTES, equipment=EquipmentEnum.BARBELL,
            increment=2.5, person_id=person.id,
        ),
        "default": ExerciseModel(
            name="Deadlift", muscle_group=MuscleGroupEnum.BACK, equipment=EquipmentEnum.BARBELL,
            increment=2.5, person_id=None,
        ),
        "other": ExerciseModel(
            name="Overhead Press", muscle_group=MuscleGroupEnum.TRICEPS, equipment=EquipmentEnum.BARBELL,
            increment=2.5, person_id=other_person.id,
        ),
    }
    db_session.add_all(exercises.values())
    db_session.commit()

    return exercises


def test_exercise_flow(create_user, db_session):
    """Test the full flow of creating, updating, and deleting an exercise."""
    client = create_user["client"]
    person = create_user["person"]

    # Create a new exercise
    response = client.post("/exercise/new", json=EXERCISE_BODY)
    assert response.status_code == 201

    # API response
    body = response.json()
    assert body["name"] == EXERCISE_BODY["name"]
    assert body["person_id"] == str(person.id)
    assert "id" in body

    # Database record
    exercise = db_session.query(ExerciseModel).one()
    assert exercise.name == EXERCISE_BODY["name"]
    assert exercise.person_id == person.id

    # Update the exercise
    update_response = client.patch(f"/exercise/id/{exercise.id}", json={"name": "Incline Bench Press"})
    assert update_response.status_code == 200
    update_body = update_response.json()
    assert update_body["name"] == "Incline Bench Press"

    # Get the exercise
    get_response = client.get(f"/exercise/id/{exercise.id}")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["name"] == "Incline Bench Press"

    # Delete the exercise
    delete_response = client.delete(f"/exercise/id/{exercise.id}")
    assert delete_response.status_code == 204
    # check that the exercise is actually deleted
    get_response = client.get(f"/exercise/id/{exercise.id}")
    assert get_response.status_code == 404 


def test_get_all_exercises(create_user, setup_exercises):
    """Test retrieving all exercises for a person."""
    client = create_user["client"]

    response = client.get("/exercise/all")
    assert response.status_code == 200
    body = response.json()
    names = {exercise["name"] for exercise in body}
    assert names == {"Squat", "Deadlift"}
    assert "Overhead Press" not in names


def test_update_delete_default_exercise(create_user, setup_exercises):
    """Test that updating and deleting a default exercise is forbidden."""
    client = create_user["client"]
    default_exercise = setup_exercises["default"]

    response = client.patch(f"/exercise/id/{default_exercise.id}", json={"name": "New Name"})
    assert response.status_code == 403
    assert response.json()["detail"] == ExerciseErrorCode.DEFAULT_EXERCISE_EDIT.value

    response = client.delete(f"/exercise/id/{default_exercise.id}")
    assert response.status_code == 403
    assert response.json()["detail"] == ExerciseErrorCode.DEFAULT_EXERCISE_DELETE.value


def test_CRUD_other_person_exercise(create_user, setup_exercises):
    """Test that updating or deleting another person's exercise returns 404."""
    client = create_user["client"]
    other_exercise = setup_exercises["other"]

    response = client.get(f"/exercise/id/{other_exercise.id}")
    assert response.status_code == 404

    response = client.patch(f"/exercise/id/{other_exercise.id}", json={"name": "New Name"})
    assert response.status_code == 404
    assert response.json()["detail"] == ExerciseErrorCode.EXERCISE_NOT_FOUND.value

    response = client.delete(f"/exercise/id/{other_exercise.id}")
    assert response.status_code == 404
    assert response.json()["detail"] == ExerciseErrorCode.EXERCISE_NOT_FOUND.value


def test_get_default_exercise_no_session(client, setup_exercises):
    """Test that default exercises can be retrieved without a session."""

    response = client.get("/exercise/all")
    assert response.status_code == 200
    body = response.json()
    names = {exercise["name"] for exercise in body}
    assert "Deadlift" in names


def test_exercise_endpoints_require_session(client, setup_exercises):
    """Test that person-scoped exercise endpoints reject an unauthenticated caller."""
    other_exercise = setup_exercises["default"]
    client.cookies.clear()  # setup_exercises authenticates this same client via create_user

    assert client.post("/exercise/new", json=EXERCISE_BODY).status_code == 401
    assert client.patch(f"/exercise/id/{other_exercise.id}", json={"name": "x"}).status_code == 401
    assert client.delete(f"/exercise/id/{other_exercise.id}").status_code == 401
    assert client.get(f"/exercise/id/{other_exercise.id}").status_code == 401


def test_delete_exercise_nulls_out_references(create_user, db_session):
    """Test that deleting an exercise clears any alternative1/alternative2 pointing to it."""
    client = create_user["client"]
    person = create_user["person"]

    alternative = ExerciseModel(
        name="Front Squat", muscle_group=MuscleGroupEnum.GLUTES, equipment=EquipmentEnum.BARBELL,
        increment=2.5, person_id=person.id,
    )
    db_session.add(alternative)
    db_session.flush()

    exercise = ExerciseModel(
        name="Squat", muscle_group=MuscleGroupEnum.GLUTES, equipment=EquipmentEnum.BARBELL,
        increment=2.5, person_id=person.id, alternative1=alternative.id,
    )
    db_session.add(exercise)
    db_session.commit()
    alternative_id, exercise_id = alternative.id, exercise.id

    response = client.delete(f"/exercise/id/{alternative_id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert db_session.scalar(select(ExerciseModel).where(ExerciseModel.id == alternative_id)) is None
    updated = db_session.scalar(select(ExerciseModel).where(ExerciseModel.id == exercise_id))
    assert updated.alternative1 is None


def test_deleting_person_cascades_to_their_exercises(create_user, db_session):
    """Test that deleting a person removes their exercises but leaves default exercises intact."""
    person = create_user["person"]

    default_exercise = ExerciseModel(
        name="Deadlift", muscle_group=MuscleGroupEnum.BACK, equipment=EquipmentEnum.BARBELL,
        increment=2.5, person_id=None,
    )
    own_exercise = ExerciseModel(
        name="Squat", muscle_group=MuscleGroupEnum.GLUTES, equipment=EquipmentEnum.BARBELL,
        increment=2.5, person_id=person.id,
    )
    db_session.add_all([default_exercise, own_exercise])
    db_session.commit()
    default_id, own_id = default_exercise.id, own_exercise.id

    db_session.delete(person)
    db_session.commit()

    db_session.expire_all()
    assert db_session.scalar(select(ExerciseModel).where(ExerciseModel.id == own_id)) is None
    assert db_session.scalar(select(ExerciseModel).where(ExerciseModel.id == default_id)) is not None