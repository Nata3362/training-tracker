import uuid
import pytest
from sqlalchemy import select

from app.authentication.models import User
from app.workout.models import StatusEnum, Workout, WorkoutExercise, WorkoutSet, Target
from app.workout.error_codes import WorkoutErrorCode
from app.person.models import Person
from app.exercise.error_codes import ExerciseErrorCode


def workout_body(own_id, default_id):
    workout = {
        'name':"Pull day",
        'date': "2026-10-14T18:30:00",
        'exercises': [
            {
            "exercise_id": str(own_id),
            "position": 1,
            "sets": [
                { "set_number": 1, "performed_weight": 60, "performed_reps": 8 },
                { "set_number": 2, "performed_weight": 65, "performed_reps": 7 }
                ] 
            },
            {
            "exercise_id": str(default_id),
            "position": 2,
            "sets": [
                { "set_number": 1, "performed_weight": 40, "performed_reps": 8 },
                { "set_number": 2, "performed_weight": 45, "performed_reps": 7 },
                { "set_number": 3, "performed_weight": 35, "performed_reps": 7 }
                ] 
            }
        ]
    }
    return workout


@pytest.fixture
def setup_target(create_user, setup_exercises, db_session):
    """Create a target for the persons own exercise"""
    person = create_user["person"]

    own_exercises = setup_exercises["own"]


    target = Target(
        person_id = person.id,
        exercise_id = own_exercises.id,
        target_weight = 25.5,
        target_reps_high = 12,
        target_reps_low = 8,
    )
    db_session.add(target)
    db_session.commit()
    return target



def test_create_workout(create_user, setup_exercises, setup_target, db_session):
    """Test the flow of creating an workout."""
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]
    target =  setup_target
    person = create_user["person"]

    targets_before = db_session.query(Target).count() # target rows before post

    # create a new workout
    payload = workout_body(own_exercise.id, default_exercise.id)
    response = client.post("/workout/new", json=payload)
    assert response.status_code == 201

    # API response
    body = response.json()
    assert body["status"] == StatusEnum.COMPLETED.value
    assert body["name"] == payload["name"]
    assert len(body["exercises"]) == len(payload["exercises"])
    assert len(body["exercises"][0]["sets"]) == len(payload["exercises"][0]["sets"])
    assert body["exercises"][0]["exercise_id"] == str(own_exercise.id)
    assert "id" in body

    own_sets = body["exercises"][0]["sets"]
    default_sets = body["exercises"][1]["sets"]

    for set_ in own_sets:
        assert set_ ["target_weight"] == target.target_weight
        assert set_ ["target_reps_high"] == target.target_reps_high
        assert set_ ["target_reps_low"] == target.target_reps_low
    for set_ in default_sets:
        assert set_ ["target_weight"] is None
        assert set_ ["target_reps_high"] is None
        assert set_ ["target_reps_low"] is None


    # Database Record
    workout = db_session.query(Workout).one()
    assert workout.name == payload["name"]
    assert workout.person_id == person.id

    workout_exercise = db_session.query(WorkoutExercise)
    assert workout_exercise.count() == len(payload["exercises"])
    
    workout_set = db_session.query(WorkoutSet)
    expected_sets = 0
    for exercise in payload["exercises"]:
        expected_sets += len(exercise["sets"])
    assert workout_set.count() == expected_sets

    target_table = db_session.query(Target)

    assert target_table.count() == targets_before

def test_create_workout_duplicate_set_number(create_user, setup_exercises, db_session):
    "Two sets with the same number in one exercise are rejected and nothing i saved."
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]

    payload = workout_body(own_exercise.id, default_exercise.id)

    # break: second set of first exercise gets the same number as the first
    payload["exercises"][0]["sets"][1]["set_number"] = 1

    response = client.post("/workout/new", json=payload)

    assert response.status_code == 422
    assert "set_number must be unique" in response.text
    assert db_session.query(Workout).count() == 0


def test_create_workout_requires_session(create_user, setup_exercises,db_session):
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]

    payload = workout_body(own_exercise.id, default_exercise.id)

    client.post("/account/logout")
    logout_response = client.get("/user")
    assert logout_response.status_code == 401

    response = client.post("/workout/new", json=payload)
    assert response.status_code == 401
    assert db_session.query(Workout).count() == 0


def test_create_workout_other_persons_exercise(create_user, create_other_person, setup_exercises, db_session):
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]
    other_person_exercise = setup_exercises["other"]

    # break: set the other_person_exercise_id instead of own_id 
    payload = workout_body(own_id=other_person_exercise.id, default_id=default_exercise.id)
    response = client.post("/workout/new", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == ExerciseErrorCode.EXERCISE_NOT_FOUND.value
    assert db_session.query(Workout).count() == 0

@pytest.mark.parametrize("field", ["name","date","exercises"])
def test_create_workout_requires_field(field, create_user, setup_exercises, db_session):
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]

    payload = workout_body(own_id=own_exercise.id, default_id=default_exercise.id)
    # break:delete date
    del payload[field]

    response = client.post("/workout/new", json=payload)
    assert response.status_code == 422
    assert db_session.query(Workout).count() == 0

def test_two_workouts_can_reuse_set_numbers(create_user, setup_exercises, db_session):
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]

    payload = workout_body(own_id=own_exercise.id, default_id=default_exercise.id)

    response = client.post("/workout/new", json=payload)
    assert response.status_code == 201
    assert db_session.query(WorkoutSet).count() == 5

    payload = workout_body(own_id=own_exercise.id, default_id=default_exercise.id)

    response = client.post("/workout/new", json=payload)
    assert response.status_code == 201
    assert db_session.query(WorkoutSet).count() == 10

def test_create_workout_duplicate_positon(create_user, setup_exercises, db_session):
    client = create_user["client"]
    own_exercise = setup_exercises["own"]
    default_exercise = setup_exercises["default"]

    payload = workout_body(own_id=own_exercise.id, default_id=default_exercise.id)
    # break: second exercise gets the same postion and the first
    payload["exercises"][1]["position"] = 1
    response = client.post("/workout/new", json=payload)

    assert response.status_code == 422
    assert "position must be unique" in response.text

    assert db_session.query(Workout).count() == 0