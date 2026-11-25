import os

from app.patterns.strategy.gemini_strategy import GeminiStrategy
from app.patterns.strategy.llm_strategy import LLMError, LLMStrategy
from app.patterns.strategy.local_inference_strategy import LocalInferenceStrategy

PROVIDERS = {
    "gemini": GeminiStrategy.from_env,
    "local": LocalInferenceStrategy.from_env,
}


def strategy_from_env() -> LLMStrategy:
    """Crea la estrategia del proveedor elegido en LLM_PROVIDER (por defecto, gemini)."""
    name = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    try:
        build = PROVIDERS[name]
    except KeyError:
        raise LLMError(f"Proveedor de LLM desconocido: {name!r}.") from None
    return build()
