import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.author import Author


class Role(enum.Enum):
    ADMIN = "admin"
    GENERAL_USER = "general_user"


class User(Author):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(ForeignKey("author.id"), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.GENERAL_USER)
    reputation: Mapped[int] = mapped_column(default=0)

    __mapper_args__ = {"polymorphic_identity": "user"}

    def get_display_name(self) -> str:
        return self.username

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)
