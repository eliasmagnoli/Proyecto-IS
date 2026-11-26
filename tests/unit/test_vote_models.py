import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Category, Question, User, Vote, VoteType


@pytest.fixture
def content(app):
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    category = Category(name="Flask")
    question = Question(
        title="¿Qué es Flask?",
        body="No entiendo.",
        author=user,
        category=category,
    )
    db.session.add(question)
    db.session.commit()

    return user, question


def test_user_can_upvote(content):
    user, question = content
    vote = Vote(user=user, content=question, value=VoteType.UPVOTE)

    db.session.add(vote)
    db.session.commit()

    assert vote.id is not None
    assert vote.value == VoteType.UPVOTE
    assert vote.user is user
    assert vote.content is question
    assert vote.created_at is not None


def test_user_can_downvote(content):
    user, question = content
    vote = Vote(user=user, content=question, value=VoteType.DOWNVOTE)

    db.session.add(vote)
    db.session.commit()

    assert vote.value == VoteType.DOWNVOTE


def test_user_cannot_vote_twice_on_same_content(content):
    user, question = content

    db.session.add(Vote(user=user, content=question, value=VoteType.UPVOTE))
    db.session.commit()

    db.session.add(Vote(user=user, content=question, value=VoteType.DOWNVOTE))

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_different_users_can_vote_on_same_content(content):
    user, question = content
    other = User(username="bob", email="bob@example.com")
    other.set_password("secreto123")

    db.session.add(other)
    db.session.commit()

    db.session.add_all(
        [
            Vote(user=user, content=question, value=VoteType.UPVOTE),
            Vote(user=other, content=question, value=VoteType.DOWNVOTE),
        ]
    )
    db.session.commit()

    assert db.session.scalar(db.select(db.func.count()).select_from(Vote)) == 2
