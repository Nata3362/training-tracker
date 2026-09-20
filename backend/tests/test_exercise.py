from app.exercise.models import ExerciseModel



EXERCISE_BODY = {
        "name": "Bench Press",
        "muscle_group": "chest",
        "equipment": "barbell",
        "increment": 2.5,
        "alternative1": None,
        "alternative2": None,
}

def test_post_exercise(create_user, db_session):
    client = create_user["client"]
    person = create_user["person"]

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

def test_update_exercise(create_user, db_session):
    client = create_user["client"]

    create_response = client.post("/exercise/new", json=EXERCISE_BODY)
    exercise_id = create_response.json()["id"]

    response = client.patch(f"/exercise/update/{exercise_id}", json={"name": "Incline Bench Press"})
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == "Incline Bench Press"

    exercise = db_session.query(ExerciseModel).one()
    assert exercise.name == "Incline Bench Press"
