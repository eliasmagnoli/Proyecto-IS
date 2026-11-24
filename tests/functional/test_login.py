from app.extensions import db
from app.models import User

CREDENTIALS = {"email": "ana@example.com", "password": "secreto123"}


def create_user():
    user = User(username="ana", email=CREDENTIALS["email"])
    user.set_password(CREDENTIALS["password"])
    db.session.add(user)
    db.session.commit()
    return user


def login(client, **overrides):
    return client.post("/users/login", json={**CREDENTIALS, **overrides})


def test_login_with_valid_credentials(client):
    create_user()

    response = login(client)

    assert response.status_code == 200
    assert response.get_json()["email"] == CREDENTIALS["email"]
    assert "password_hash" not in response.get_json()


def test_login_email_is_case_insensitive(client):
    create_user()

    assert login(client, email="ANA@Example.com").status_code == 200


def test_login_with_wrong_password_fails(client):
    create_user()

    response = login(client, password="incorrecta")

    assert response.status_code == 401
    assert client.get("/users/me").status_code == 401


def test_login_with_unknown_email_gives_same_error(client):
    create_user()

    wrong_password = login(client, password="incorrecta")
    unknown_email = login(client, email="nadie@example.com")

    assert unknown_email.status_code == 401
    assert unknown_email.get_json() == wrong_password.get_json()


def test_login_with_missing_fields_fails(client):
    response = client.post("/users/login", json={})

    assert response.status_code == 401


def test_me_requires_login(client):
    assert client.get("/users/me").status_code == 401


def test_me_returns_logged_in_user(client):
    create_user()
    login(client)

    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.get_json()["username"] == "ana"


def test_logout_closes_session(client):
    create_user()
    login(client)

    response = client.post("/users/logout")

    assert response.status_code == 204
    assert client.get("/users/me").status_code == 401


def test_session_of_deleted_user_is_rejected(client):
    user = create_user()
    login(client)
    db.session.delete(user)
    db.session.commit()

    assert client.get("/users/me").status_code == 401
