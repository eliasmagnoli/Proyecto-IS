import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import AIAgent, Category, Question, Response, Tag, User, VotableContent


@pytest.fixture
def base(app):
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    category = Category(name="Flask", description="Todo sobre Flask")
    db.session.add_all([user, category])
    db.session.commit()
    return user, category


def make_question(user, category, **kwargs):
    question = Question(
        title="¿Qué es un blueprint?", body="No entiendo.", author=user, category=category
    )
    for key, value in kwargs.items():
        setattr(question, key, value)
    db.session.add(question)
    db.session.commit()
    return question


def test_question_has_category_author_tags_and_automatic_date(base):
    user, category = base
    tags = [Tag(name="blueprint"), Tag(name="flask")]

    question = make_question(user, category, tags=tags)

    assert question.published_at is not None
    assert question.category.name == "Flask"
    assert question.author.username == "ana"
    assert {tag.name for tag in question.tags} == {"blueprint", "flask"}


def test_question_requires_a_category(base):
    user, _ = base
    db.session.add(Question(title="Sin categoría", body="x", author=user))

    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_category_and_tag_names_are_unique(base):
    db.session.add(Category(name="Flask"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

    db.session.add_all([Tag(name="dup"), Tag(name="dup")])
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_response_can_be_written_by_a_user_or_an_ai_agent(base):
    user, category = base
    question = make_question(user, category)
    agent = AIAgent(agent_name="helper", model_version="v1")
    db.session.add(agent)
    db.session.commit()

    db.session.add_all(
        [
            Response(body="De una persona", question=question, author=user),
            Response(body="De la IA", question=question, author=agent),
        ]
    )
    db.session.commit()
    db.session.expire_all()

    authors = {r.author.get_display_name() for r in question.responses}
    assert authors == {"ana", "helper"}


def test_deleting_a_question_deletes_its_responses(base):
    user, category = base
    question = make_question(user, category)
    db.session.add(Response(body="x", question=question, author=user))
    db.session.commit()

    db.session.delete(question)
    db.session.commit()

    assert db.session.scalar(db.select(db.func.count()).select_from(Response)) == 0


def test_is_resolved_is_derived_from_responses(base):
    user, category = base
    question = make_question(user, category)
    response = Response(body="x", question=question, author=user)
    db.session.add(response)
    db.session.commit()
    assert question.is_resolved is False

    response.is_accepted = True
    db.session.commit()
    assert question.is_resolved is True


def test_votable_content_query_returns_questions_and_responses(base):
    user, category = base
    question = make_question(user, category)
    db.session.add(Response(body="x", question=question, author=user))
    db.session.commit()

    contents = db.session.scalars(db.select(VotableContent)).all()

    assert {type(c) for c in contents} == {Question, Response}


def test_agent_can_have_trigger_tags(base):
    tag = Tag(name="ia-help")
    agent = AIAgent(agent_name="helper", model_version="v1", trigger_tags=[tag])
    db.session.add(agent)
    db.session.commit()
    db.session.expire_all()

    loaded = db.session.scalar(db.select(AIAgent))
    assert [t.name for t in loaded.trigger_tags] == ["ia-help"]
