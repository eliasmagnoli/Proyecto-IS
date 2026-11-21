from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.author import Author


class AIAgent(Author):
    __tablename__ = "ai_agent"

    id: Mapped[int] = mapped_column(ForeignKey("author.id"), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(80))
    timeout_minutes: Mapped[int] = mapped_column(default=60)

    __mapper_args__ = {"polymorphic_identity": "ai_agent"}

    def get_display_name(self) -> str:
        return self.agent_name
