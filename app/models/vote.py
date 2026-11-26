import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.user import User

if TYPE_CHECKING:
    from app.models.votable_content import VotableContent


class VoteType(enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class Vote(db.Model):
    __tablename__ = "vote"
    __table_args__ = (UniqueConstraint("user_id", "content_id", name="uq_vote_user_content"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[VoteType] = mapped_column(Enum(VoteType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content_id: Mapped[int] = mapped_column(ForeignKey("votable_content.id"), nullable=False)

    user: Mapped[User] = relationship()
    content: Mapped["VotableContent"] = relationship(back_populates="votes")
