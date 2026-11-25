from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

# Tablas intermedias de las relaciones muchos a muchos.
question_tags = Table(
    "question_tags",
    db.metadata,
    Column("question_id", ForeignKey("question.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)

agent_tags = Table(
    "agent_tags",
    db.metadata,
    Column("agent_id", ForeignKey("ai_agent.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
