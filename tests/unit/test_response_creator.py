import pytest

from app.extensions import db
from app.models import AIAgent, Category, Question, Response, User
from app.patterns.factory.ai_response_creator import AIResponseCreator
from app.patterns.factory.human_response_creator import HumanResponseCreator
from app.patterns.factory.response_creator import ResponseCreator
from app.patterns.strategy.fake_strategy import FakeStrategy


@pytest.fixture
def question(app):
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    category = Category(name="Flask")
    question = Question(title="¿Qué es un blueprint?", body="No entiendo.", author=user)
    question.category = category
    db.session.add(question)
    db.session.commit()
    return question


@pytest.fixture
def agent(app):
    agent = AIAgent(agent_name="helper", model_version="v1")
    db.session.add(agent)
    db.session.commit()
    return agent


def count_responses():
    return db.session.scalar(db.select(db.func.count()).select_from(Response))


def test_response_creator_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ResponseCreator()


def test_human_creator_publishes_response_with_the_user_as_author(question):
    bob = User(username="bob", email="bob@example.com")
    bob.set_password("secreto123")
    db.session.add(bob)
    db.session.commit()

    response = HumanResponseCreator(bob).publish_response(question, "  Agrupa rutas.  ")

    assert response.id is not None
    assert response.body == "Agrupa rutas."
    assert response.author is bob
    assert response.question is question
    assert response.published_at is not None
    assert count_responses() == 1


def test_human_creator_rejects_empty_content_and_saves_nothing(question):
    creator = HumanResponseCreator(question.author)

    for empty in (None, "", "   "):
        with pytest.raises(ValueError):
            creator.publish_response(question, empty)

    assert count_responses() == 0


def test_ai_creator_uses_the_agent_text_and_ignores_raw_content(question, agent):
    fake = FakeStrategy(response="Texto de la IA")
    agent.set_strategy(fake)

    response = AIResponseCreator(agent).publish_response(question, "esto se ignora")

    assert response.body == "Texto de la IA"
    assert response.author is agent
    assert len(fake.calls) == 1
    assert count_responses() == 1


def test_a_new_creator_needs_no_changes_to_response_or_response_creator(question):
    class UppercaseCreator(ResponseCreator):
        def _resolve_content(self, question, raw_content):
            return (raw_content or "").upper()

        def _create_response(self, question, content):
            return Response(body=content, question=question, author=question.author)

    response = UppercaseCreator().publish_response(question, "hola")

    assert response.body == "HOLA"
