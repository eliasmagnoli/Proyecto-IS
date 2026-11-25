from abc import ABC, abstractmethod


class LLMError(Exception):
    """Falla al generar texto con un proveedor de LLM."""


class LLMStrategy(ABC):
    @abstractmethod
    def generate_completion(self, prompt: str, context: str) -> str:
        """Devuelve el texto generado a partir de la consigna y el contexto."""
