import httpx
import pytest

from app.patterns.strategy.gemini_strategy import GeminiStrategy
from app.patterns.strategy.llm_strategy import LLMError

GOOD_BODY = {"candidates": [{"content": {"parts": [{"text": "Respuesta del modelo"}]}}]}


def make_strategy(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return GeminiStrategy(api_key="clave-secreta", model_name="modelo-x", client=client)


def test_generate_completion_returns_text_and_sends_expected_request():
    sent = {}

    def handler(request):
        sent["url"] = str(request.url)
        sent["key"] = request.headers["x-goog-api-key"]
        sent["body"] = request.content.decode()
        return httpx.Response(200, json=GOOD_BODY)

    text = make_strategy(handler).generate_completion("consigna", "contexto")

    assert text == "Respuesta del modelo"
    assert sent["url"].endswith("/models/modelo-x:generateContent")
    assert "clave-secreta" not in sent["url"]
    assert sent["key"] == "clave-secreta"
    assert "consigna" in sent["body"] and "contexto" in sent["body"]


def test_http_error_becomes_llm_error_without_leaking_the_key():
    strategy = make_strategy(lambda request: httpx.Response(500, json={}))

    with pytest.raises(LLMError) as error:
        strategy.generate_completion("p", "c")

    assert "500" in str(error.value)
    assert "clave-secreta" not in str(error.value)


def test_network_failure_becomes_llm_error():
    def handler(request):
        raise httpx.ConnectError("sin red")

    with pytest.raises(LLMError):
        make_strategy(handler).generate_completion("p", "c")


def test_unexpected_response_shape_becomes_llm_error():
    strategy = make_strategy(lambda request: httpx.Response(200, json={"candidates": []}))

    with pytest.raises(LLMError):
        strategy.generate_completion("p", "c")


def test_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(LLMError):
        GeminiStrategy.from_env()


def test_from_env_reads_key_and_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "abc")
    monkeypatch.setenv("GEMINI_MODEL", "otro-modelo")

    strategy = GeminiStrategy.from_env()

    assert strategy.api_key == "abc"
    assert strategy.model_name == "otro-modelo"
