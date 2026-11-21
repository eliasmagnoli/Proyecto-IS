from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Author(db.Model):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_abstract": True,
    }

    def get_display_name(self) -> str:
        raise NotImplementedError
