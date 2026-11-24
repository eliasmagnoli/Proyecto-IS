import re

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


class RegistrationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid registration data")
        self.errors = errors


def _clean(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def validate_registration(username: str, email: str, password: str) -> dict[str, str]:
    errors = {}

    if not 3 <= len(username) <= 50:
        errors["username"] = "El nombre debe tener entre 3 y 50 caracteres."
    elif db.session.scalar(db.select(User).filter_by(username=username)):
        errors["username"] = "Ese nombre de usuario ya está en uso."

    if not EMAIL_PATTERN.match(email) or len(email) > 120:
        errors["email"] = "El email no es válido."
    elif db.session.scalar(db.select(User).filter_by(email=email)):
        errors["email"] = "Ese email ya está registrado."

    if len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."

    return errors


def register_user(username, email, password) -> User:
    username = _clean(username)
    email = _clean(email).lower()
    password = password if isinstance(password, str) else ""

    errors = validate_registration(username, email, password)
    if errors:
        raise RegistrationError(errors)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        # Otro registro con el mismo dato se coló entre la validación y el commit.
        db.session.rollback()
        raise RegistrationError({"email": "Ese email o nombre de usuario ya está en uso."})

    return user


def authenticate(email, password) -> User | None:
    email = _clean(email).lower()
    if not email or not isinstance(password, str):
        return None

    user = db.session.scalar(db.select(User).filter_by(email=email))
    if user is None or not user.check_password(password):
        return None
    return user
