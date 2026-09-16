from conftest import create_user


def test_me(create_user):
    client = create_user["client"]
    person = create_user["person"]

    response = client.get("/person/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(person.id)
