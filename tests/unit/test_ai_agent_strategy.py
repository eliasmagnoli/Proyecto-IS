from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models import AIAgent
from app.patterns.strategy.fake_strategy import FakeStrategy

QUESTION = SimpleNamespace(title="¿Qué es un blueprint?", body="No entiendo para qué sirven.")


def make_agent():
    return AIAgent(agent_name="helper", model_version="v1")


def test_agent_generates_response_through_its_strategy():
    agent = make_agent()
    fake = FakeStrategy(response="Un blueprint agrupa rutas.")
    agent.set_strategy(fake)

    assert agent.generate_auto_response(QUESTION) == "Un blueprint agrupa rutas."
    _, context = fake.calls[0]
    assert "¿Qué es un blueprint?" in context and "No entiendo" in context


def test_agent_without_strategy_fails_clearly():
    with pytest.raises(RuntimeError):
        make_agent().generate_auto_response(QUESTION)


def test_strategy_is_not_persisted_and_agent_still_loads(app):
    agent = make_agent()
    agent.set_strategy(FakeStrategy())
    db.session.add(agent)
    db.session.commit()
    db.session.expunge_all()

    loaded = db.session.scalar(db.select(AIAgent))

    with pytest.raises(RuntimeError):
        loaded.generate_auto_response(QUESTION)
