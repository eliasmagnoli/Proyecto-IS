import os

import httpx

from app.patterns.strategy.llm_strategy import LLMError, LLMStrategy

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiStrategy(LLMStrategy):
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        client: httpx.Client | None = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self._client = client or httpx.Client(timeout=30)

    @classmethod
    def from_env(cls) -> "GeminiStrategy":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMError("Falta la variable de entorno GEMINI_API_KEY.")
        return cls(api_key, os.environ.get("GEMINI_MODEL", DEFAULT_MODEL))

    def generate_completion(self, prompt: str, context: str) -> str:
        url = f"{BASE_URL}/{self.model_name}:generateContent"
        body = {
            "system_instruction": {"parts": [{"text": prompt}]},
            "contents": [{"parts": [{"text": context}]}],
        }

        try:
            response = self._client.post(url, json=body, headers={"x-goog-api-key": self.api_key})
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as error:
            raise LLMError(f"Gemini respondió con error {error.response.status_code}.") from error
        except httpx.HTTPError as error:
            raise LLMError("No se pudo conectar con Gemini.") from error
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise LLMError("Respuesta inesperada de Gemini.") from error
