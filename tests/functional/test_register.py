from app.extensions import db
from app.models import Role, User

VALID = {"username": "ana", "email": "ana@example.com", "password": "secreto123"}


def post_register(client, **overrides):
    return client.post("/users/register", json={**VALID, **overrides})


def test_register_creates_user_with_default_role(client):
    response = post_register(client)

    assert response.status_code == 201
    assert response.get_json()["role"] == "general_user"
    user = db.session.scalar(db.select(User).filter_by(email="ana@example.com"))
    assert user.role == Role.GENERAL_USER


def test_register_does_not_store_plain_password(client):
    post_register(client)

    user = db.session.scalar(db.select(User).filter_by(username="ana"))
    assert user.password_hash != VALID["password"]
    assert user.check_password(VALID["password"])


def test_register_response_never_includes_password(client):
    body = post_register(client).get_json()

    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email_ignoring_case(client):
    post_register(client)

    response = post_register(client, username="otra", email="ANA@example.com")

    assert response.status_code == 400
    assert "email" in response.get_json()["errors"]


def test_register_rejects_duplicate_username(client):
    post_register(client)

    response = post_register(client, email="otra@example.com")

    assert response.status_code == 400
    assert "username" in response.get_json()["errors"]


def test_register_reports_all_validation_errors(client):
    response = client.post(
        "/users/register", json={"username": "a", "email": "no-es-email", "password": "123"}
    )

    assert response.status_code == 400
    assert set(response.get_json()["errors"]) == {"username", "email", "password"}


def test_register_requires_all_fields(client):
    response = client.post("/users/register", json={})

    assert response.status_code == 400
    assert set(response.get_json()["errors"]) == {"username", "email", "password"}
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0
