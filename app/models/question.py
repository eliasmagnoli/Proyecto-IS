from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.category import Category
from app.models.tag import Tag, question_tags
from app.models.user import User
from app.models.votable_content import VotableContent

if TYPE_CHECKING:
    from app.models.response import Response


class Question(VotableContent):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(ForeignKey("votable_content.id"), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    __mapper_args__ = {"polymorphic_identity": "question"}

    category: Mapped[Category] = relationship()
    author: Mapped[User] = relationship()
    tags: Mapped[list[Tag]] = relationship(secondary=question_tags)
    responses: Mapped[list["Response"]] = relationship(
        back_populates="question",
        foreign_keys="Response.question_id",
        cascade="all, delete-orphan",
    )

    @property
    def is_resolved(self) -> bool:
        return any(response.is_accepted for response in self.responses)
