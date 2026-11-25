import logging

import pytest

from app.extensions import db
from app.models import AIAgent, Category, Question, Response, Tag, User
from app.patterns.strategy.fake_strategy import FakeStrategy
from app.patterns.strategy.gemini_strategy import GeminiStrategy
from app.patterns.strategy.llm_strategy import LLMError
from app.patterns.strategy.local_inference_strategy import LocalInferenceStrategy
from app.patterns.strategy.provider import strategy_from_env
from app.services.ai_agent_triggers import trigger_agents


@pytest.fixture
def ia_help(app):
    tag = Tag(name="ia-help")
    db.session.add(tag)
    db.session.commit()
    return tag


@pytest.fixture
def agent(ia_help):
    agent = AIAgent(agent_name="helper", model_version="v1", trigger_tags=[ia_help])
    db.session.add(agent)
    db.session.commit()
    return agent


def make_question(tags):
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    question = Question(
        title="¿Qué es un blueprint?",
        body="No entiendo.",
        author=user,
        category=Category(name="Flask"),
        tags=tags,
    )
    db.session.add(question)
    db.session.commit()
    return question


def count_responses():
    return db.session.scalar(db.select(db.func.count()).select_from(Response))


def test_tagged_question_gets_a_response_from_the_agent(agent, ia_help):
    question = make_question([ia_help])

    responses = trigger_agents(question, lambda: FakeStrategy(response="Respuesta de la IA"))

    assert len(responses) == 1
    assert responses[0].author is agent
    assert responses[0].body == "Respuesta de la IA"
    assert responses[0].question is question


def test_question_without_tags_triggers_nothing(agent):
    calls = []
    question = make_question([])

    responses = trigger_agents(question, lambda: calls.append(1) or FakeStrategy())

    assert responses == []
    assert calls == []
    assert count_responses() == 0


def test_tag_not_linked_to_any_agent_triggers_nothing(agent):
    question = make_question([Tag(name="python")])

    assert trigger_agents(question, FakeStrategy) == []
    assert count_responses() == 0


def test_llm_failure_keeps_the_question_and_logs_the_error(agent, ia_help, caplog):
    question = make_question([ia_help])

    with caplog.at_level(logging.ERROR):
        responses = trigger_agents(question, lambda: FakeStrategy(fail=True))

    assert responses == []
    assert count_responses() == 0
    assert db.session.get(Question, question.id) is not None
    assert "helper" in caplog.text


def test_missing_credentials_are_also_handled(agent, ia_help, caplog):
    question = make_question([ia_help])

    def no_credentials():
        raise LLMError("Falta la clave.")

    with caplog.at_level(logging.ERROR):
        assert trigger_agents(question, no_credentials) == []

    assert db.session.get(Question, question.id) is not None
    assert "helper" in caplog.text


def test_one_failing_agent_does_not_stop_the_others(agent, ia_help):
    second = AIAgent(agent_name="second", model_version="v1", trigger_tags=[ia_help])
    db.session.add(second)
    db.session.commit()
    question = make_question([ia_help])
    strategies = iter([FakeStrategy(fail=True), FakeStrategy(response="ok")])

    responses = trigger_agents(question, lambda: next(strategies))

    assert len(responses) == 1
    assert responses[0].body == "ok"


def test_agent_does_not_answer_the_same_question_twice(agent, ia_help):
    question = make_question([ia_help])

    first = trigger_agents(question, FakeStrategy)
    second = trigger_agents(question, FakeStrategy)

    assert len(first) == 1
    assert second == []
    assert count_responses() == 1


def test_strategy_from_env_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "abc")

    assert isinstance(strategy_from_env(), GeminiStrategy)


def test_strategy_from_env_can_select_the_local_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "local")

    assert isinstance(strategy_from_env(), LocalInferenceStrategy)


def test_strategy_from_env_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "otro")

    with pytest.raises(LLMError):
        strategy_from_env()
