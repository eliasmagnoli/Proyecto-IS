from flask import Blueprint, jsonify, request

from app.blueprints.users.services import RegistrationError, register_user

bp = Blueprint("users", __name__, url_prefix="/users")


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

    return (
        jsonify(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
            }
        ),
        201,
    )
