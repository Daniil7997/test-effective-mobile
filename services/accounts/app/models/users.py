import uuid
from datetime import datetime
import enum

from sqlalchemy.orm import (MappedAsDataclass,
                            DeclarativeBase,
                            Mapped,
                            mapped_column)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (String,
                        func,
                        Enum)


class UserRole(enum.StrEnum):
    admin = "admin"
    user = "user"


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class AuthUsers(Base):
    __tablename__ = "auth_users"

    user_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        insert_default=uuid.uuid7,
        init=False
    )
    email: Mapped[str] = mapped_column(String(50),
                                       unique=True,
                                       nullable=False)
    password: Mapped[str] = mapped_column(String(255),
                                          nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False),
                                           default=UserRole.user,
                                           nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True,
                                            nullable=False,
                                            init=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(),
                                                 onupdate=func.now())
