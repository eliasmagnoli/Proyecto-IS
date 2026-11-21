from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class VotableContent(db.Model):
    __tablename__ = "votable_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_abstract": True,
    }
