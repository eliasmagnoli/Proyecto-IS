from functools import wraps

from flask import jsonify, session

from app.extensions import db
from app.models import User


def current_user() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None

    user = db.session.get(User, user_id)
    if user is None:
        # La sesión apunta a un usuario que ya no existe.
        session.clear()
    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Authentication required."}), 401
        return view(*args, **kwargs)

    return wrapped
