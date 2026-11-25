from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.author import Author
from app.models.tag import Tag, agent_tags
from app.patterns.strategy.llm_strategy import LLMStrategy

DEFAULT_PROMPT = (
    "Sos un asistente que responde preguntas de estudiantes universitarios en una "
    "plataforma de preguntas y respuestas. Respondé en español, de forma clara y concisa."
)


class AIAgent(Author):
    __tablename__ = "ai_agent"

    id: Mapped[int] = mapped_column(ForeignKey("author.id"), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(80))
    timeout_minutes: Mapped[int] = mapped_column(default=60)

    __mapper_args__ = {"polymorphic_identity": "ai_agent"}
    trigger_tags: Mapped[list[Tag]] = relationship(secondary=agent_tags)

    # La estrategia no se guarda en la base: se asigna en tiempo de ejecución.
    _strategy = None

    def get_display_name(self) -> str:
        return self.agent_name

    def set_strategy(self, strategy: LLMStrategy) -> None:
        self._strategy = strategy

    def generate_auto_response(self, question) -> str:
        if self._strategy is None:
            raise RuntimeError("El agente no tiene una estrategia de LLM asignada.")

        context = f"{question.title}\n\n{question.body}"
        return self._strategy.generate_completion(DEFAULT_PROMPT, context)
