import uuid
import enum
from datetime import datetime

from sqlalchemy.orm import (MappedAsDataclass,
                            DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, func, DateTime


class UserRole(enum.StrEnum):
    admin = "admin"
    user = "user"


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class UserData(Base):
    __tablename__ = "user_data"

    user_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        init=True
    )
    username: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(),
                                                 default=func.now(),
                                                 init=False)
    posts: Mapped[list["Posts"]] = relationship(
        "Posts", back_populates="author", init=False)


class Posts(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_data.user_uuid"),
        init=True
    )
    title: Mapped[str] = mapped_column(String(30), init=True)
    content: Mapped[str] = mapped_column(String(750), init=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(),
                                                 default=func.now(),
                                                 init=False)
    author: Mapped["UserData"] = relationship(
        "UserData", back_populates="posts", init=False)
