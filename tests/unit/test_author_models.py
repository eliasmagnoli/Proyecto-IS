import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import AIAgent, Author, Role, User


def make_user():
    user = User(username="ana", email="ana@example.com")
    user.set_password("secret")
    return user


def test_polymorphic_query_returns_subclasses(app):
    agent = AIAgent(agent_name="helper", model_version="v1", timeout_minutes=30)
    db.session.add_all([make_user(), agent])
    db.session.commit()

    authors = db.session.scalars(db.select(Author)).all()

    assert {type(a) for a in authors} == {User, AIAgent}
    assert {a.get_display_name() for a in authors} == {"ana", "helper"}


def test_user_defaults_and_password_hash(app):
    user = make_user()
    db.session.add(user)
    db.session.commit()

    assert user.role == Role.GENERAL_USER
    assert user.reputation == 0
    assert user.password_hash != "secret"
    assert user.check_password("secret")
    assert not user.check_password("otra")


def test_email_must_be_unique(app):
    db.session.add(make_user())
    db.session.commit()

    duplicate = User(username="otra", email="ana@example.com")
    duplicate.set_password("x")
    db.session.add(duplicate)

    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
