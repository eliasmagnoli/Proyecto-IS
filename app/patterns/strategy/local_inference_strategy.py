import os

import httpx

from app.patterns.strategy.llm_strategy import LLMError, LLMStrategy

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"


class LocalInferenceStrategy(LLMStrategy):
    """Usa un modelo que corre en la propia máquina a través de Ollama."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.Client | None = None,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        # Un modelo local puede tardar bastante más que una API en la nube.
        self._client = client or httpx.Client(timeout=120)

    @classmethod
    def from_env(cls) -> "LocalInferenceStrategy":
        return cls(
            os.environ.get("LOCAL_LLM_MODEL", DEFAULT_MODEL),
            os.environ.get("LOCAL_LLM_URL", DEFAULT_BASE_URL),
        )

    def generate_completion(self, prompt: str, context: str) -> str:
        body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            "stream": False,
        }

        try:
            response = self._client.post(f"{self.base_url}/api/chat", json=body)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.HTTPStatusError as error:
            raise LLMError(
                f"El modelo local respondió con error {error.response.status_code}."
            ) from error
        except httpx.HTTPError as error:
            raise LLMError(
                "No se pudo conectar con el modelo local (¿está corriendo Ollama?)."
            ) from error
        except (KeyError, TypeError, ValueError) as error:
            raise LLMError("Respuesta inesperada del modelo local.") from error
