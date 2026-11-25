import httpx
import pytest

from app.patterns.strategy.llm_strategy import LLMError
from app.patterns.strategy.local_inference_strategy import LocalInferenceStrategy

GOOD_BODY = {"message": {"role": "assistant", "content": "Respuesta local"}}


def make_strategy(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return LocalInferenceStrategy(
        model_name="modelo-x", base_url="http://local:1234/", client=client
    )


def test_generate_completion_returns_text_and_sends_expected_request():
    sent = {}

    def handler(request):
        sent["url"] = str(request.url)
        sent["body"] = request.content.decode()
        return httpx.Response(200, json=GOOD_BODY)

    text = make_strategy(handler).generate_completion("consigna", "contexto")

    assert text == "Respuesta local"
    assert sent["url"] == "http://local:1234/api/chat"
    assert '"modelo-x"' in sent["body"]
    assert '"stream":false' in sent["body"].replace(" ", "")
    assert "consigna" in sent["body"] and "contexto" in sent["body"]


def test_http_error_becomes_llm_error():
    strategy = make_strategy(lambda request: httpx.Response(404, json={}))

    with pytest.raises(LLMError) as error:
        strategy.generate_completion("p", "c")

    assert "404" in str(error.value)


def test_server_not_running_becomes_llm_error():
    def handler(request):
        raise httpx.ConnectError("conexión rechazada")

    with pytest.raises(LLMError):
        make_strategy(handler).generate_completion("p", "c")


def test_unexpected_response_shape_becomes_llm_error():
    strategy = make_strategy(lambda request: httpx.Response(200, json={"otro": "formato"}))

    with pytest.raises(LLMError):
        strategy.generate_completion("p", "c")


def test_from_env_uses_defaults_and_overrides(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_MODEL", raising=False)
    monkeypatch.delenv("LOCAL_LLM_URL", raising=False)
    default = LocalInferenceStrategy.from_env()
    assert (default.model_name, default.base_url) == ("llama3.2", "http://localhost:11434")

    monkeypatch.setenv("LOCAL_LLM_MODEL", "otro")
    monkeypatch.setenv("LOCAL_LLM_URL", "http://otra:1/")
    custom = LocalInferenceStrategy.from_env()
    assert (custom.model_name, custom.base_url) == ("otro", "http://otra:1")
