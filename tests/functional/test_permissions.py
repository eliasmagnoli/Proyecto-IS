import pytest
from flask import jsonify

from app.blueprints.users.auth import role_required
from app.extensions import db
from app.models import Role, User


@pytest.fixture(autouse=True)
def protected_routes(app):
    @app.get("/test/admin-only")
    @role_required(Role.ADMIN)
    def admin_only():
        return jsonify({"ok": True})

    @app.get("/test/any-role")
    @role_required(Role.ADMIN, Role.GENERAL_USER)
    def any_role():
        return jsonify({"ok": True})


def login_as(client, role):
    user = User(username=role.value, email=f"{role.value}@example.com", role=role)
    user.set_password("secreto123")
    db.session.add(user)
    db.session.commit()
    client.post("/users/login", json={"email": user.email, "password": "secreto123"})


def test_anonymous_gets_401(client):
    assert client.get("/test/admin-only").status_code == 401


def test_general_user_gets_403_on_admin_route(client):
    login_as(client, Role.GENERAL_USER)

    assert client.get("/test/admin-only").status_code == 403


def test_admin_can_access_admin_route(client):
    login_as(client, Role.ADMIN)

    response = client.get("/test/admin-only")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_route_can_allow_several_roles(client):
    login_as(client, Role.GENERAL_USER)

    assert client.get("/test/any-role").status_code == 200


def test_role_change_takes_effect_immediately(client):
    login_as(client, Role.ADMIN)
    assert client.get("/test/admin-only").status_code == 200

    user = db.session.scalar(db.select(User).filter_by(username="admin"))
    user.role = Role.GENERAL_USER
    db.session.commit()

    assert client.get("/test/admin-only").status_code == 403
