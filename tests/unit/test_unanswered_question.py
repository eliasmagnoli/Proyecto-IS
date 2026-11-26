import logging
from datetime import timedelta

import pytest

from app.extensions import db
from app.models import AIAgent, Category, Question, Response, User
from app.patterns.strategy.fake_strategy import FakeStrategy
from app.services.ai_agent_triggers import respond_to_unanswered_questions


@pytest.fixture
def question(app):
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    question = Question(
        title="¿Qué es un blueprint?",
        body="No entiendo.",
        author=user,
        category=Category(name="Flask"),
    )
    db.session.add(question)
    db.session.commit()
    return question


def make_agent(name="helper", timeout=60):
    agent = AIAgent(agent_name=name, model_version="v1", timeout_minutes=timeout)
    db.session.add(agent)
    db.session.commit()
    return agent


def count_responses():
    return db.session.scalar(db.select(db.func.count()).select_from(Response))


def after(question, minutes):
    return question.published_at + timedelta(minutes=minutes)


def test_agent_answers_a_question_that_waited_longer_than_its_timeout(question):
    agent = make_agent(timeout=60)

    responses = respond_to_unanswered_questions(after(question, 61), FakeStrategy)

    assert len(responses) == 1
    assert responses[0].author is agent
    assert responses[0].question is question


def test_question_that_has_not_waited_enough_is_left_alone(question):
    make_agent(timeout=60)

    assert respond_to_unanswered_questions(after(question, 30), FakeStrategy) == []
    assert count_responses() == 0


def test_question_that_already_has_a_response_is_not_answered(question):
    make_agent(timeout=60)
    db.session.add(Response(body="De una persona", question=question, author=question.author))
    db.session.commit()

    assert respond_to_unanswered_questions(after(question, 600), FakeStrategy) == []
    assert count_responses() == 1


def test_agent_does_not_answer_the_same_question_twice(question):
    make_agent(timeout=60)
    now = after(question, 61)

    first = respond_to_unanswered_questions(now, FakeStrategy)
    second = respond_to_unanswered_questions(now, FakeStrategy)

    assert len(first) == 1
    assert second == []
    assert count_responses() == 1


def test_each_agent_uses_its_own_timeout(question):
    make_agent("slow", timeout=100)
    fast = make_agent("fast", timeout=10)

    responses = respond_to_unanswered_questions(after(question, 50), FakeStrategy)

    assert [r.author for r in responses] == [fast]


def test_only_one_agent_answers_when_several_are_eligible(question):
    make_agent("slow", timeout=100)
    fast = make_agent("fast", timeout=10)

    responses = respond_to_unanswered_questions(after(question, 500), FakeStrategy)

    assert [r.author for r in responses] == [fast]
    assert count_responses() == 1


def test_llm_failure_is_logged_and_retried_on_the_next_run(question, caplog):
    make_agent(timeout=60)
    now = after(question, 61)

    with caplog.at_level(logging.ERROR):
        assert respond_to_unanswered_questions(now, lambda: FakeStrategy(fail=True)) == []
    assert "helper" in caplog.text
    assert count_responses() == 0

    retry = respond_to_unanswered_questions(now, FakeStrategy)
    assert len(retry) == 1
