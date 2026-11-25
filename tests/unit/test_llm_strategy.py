import pytest

from app.patterns.strategy.fake_strategy import FakeStrategy
from app.patterns.strategy.llm_strategy import LLMError, LLMStrategy


def test_llm_strategy_cannot_be_instantiated():
    with pytest.raises(TypeError):
        LLMStrategy()


def test_fake_strategy_returns_configured_response_and_records_calls():
    strategy = FakeStrategy(response="hola")

    assert strategy.generate_completion("consigna", "contexto") == "hola"
    assert strategy.calls == [("consigna", "contexto")]


def test_fake_strategy_can_fail():
    with pytest.raises(LLMError):
        FakeStrategy(fail=True).generate_completion("p", "c")
