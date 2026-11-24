from flask import Blueprint, jsonify, request, session

from app.blueprints.users.auth import current_user, login_required
from app.blueprints.users.services import RegistrationError, authenticate, register_user

bp = Blueprint("users", __name__, url_prefix="/users")


def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
    }


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    try:
        user = register_user(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password"),
        )
    except RegistrationError as error:
        return jsonify({"errors": error.errors}), 400

    return jsonify(user_to_dict(user)), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    user = authenticate(data.get("email"), data.get("password"))
    if user is None:
        return jsonify({"error": "Email o contraseña incorrectos."}), 401

    session.clear()
    session["user_id"] = user.id
    return jsonify(user_to_dict(user)), 200


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/me")
@login_required
def me():
    return jsonify(user_to_dict(current_user())), 200
