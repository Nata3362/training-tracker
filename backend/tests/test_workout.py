import uuid
import pytest
from sqlalchemy import select

from app.authentication.models import User
from app.workout.models import StatusEnum, Workout, WorkoutExercise, WorkoutSet, Target
from app.workout.error_codes import WorkoutErrorCode
from app.person.models import Person


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

