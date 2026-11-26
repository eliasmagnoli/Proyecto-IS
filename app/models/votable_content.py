from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.vote import VoteType

if TYPE_CHECKING:
    from app.models.vote import Vote


class VotableContent(db.Model):
    __tablename__ = "votable_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    votes: Mapped[list["Vote"]] = relationship(back_populates="content")

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_abstract": True,
    }

    def calculate_score(self) -> int:
        upvotes = sum(vote.value == VoteType.UPVOTE for vote in self.votes)
        downvotes = sum(vote.value == VoteType.DOWNVOTE for vote in self.votes)
        return upvotes - downvotes
