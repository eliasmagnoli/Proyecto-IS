from app.patterns.strategy.llm_strategy import LLMError, LLMStrategy


class FakeStrategy(LLMStrategy):
    """Estrategia simulada para tests: no llama a ningún proveedor."""

    def __init__(self, response: str = "respuesta simulada", fail: bool = False):
        self.response = response
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def generate_completion(self, prompt: str, context: str) -> str:
        self.calls.append((prompt, context))
        if self.fail:
            raise LLMError("fallo simulado")
        return self.response
