from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.author import Author
from app.models.question import Question
from app.models.votable_content import VotableContent


class Response(VotableContent):
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(ForeignKey("votable_content.id"), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    is_accepted: Mapped[bool] = mapped_column(default=False)

    __mapper_args__ = {"polymorphic_identity": "response"}

    question: Mapped[Question] = relationship(
        back_populates="responses", foreign_keys=[question_id]
    )
    author: Mapped[Author] = relationship(foreign_keys=[author_id])
