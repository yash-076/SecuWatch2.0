from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    class Role(str, Enum):
        ADMIN = "admin"
        ANALYST = "analyst"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="user_role", native_enum=False),
        nullable=False,
        default=Role.ANALYST,
    )
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    devices = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    organization = relationship("Organization", back_populates="users")
    assigned_alerts = relationship(
        "Alert",
        back_populates="assignee",
        foreign_keys="Alert.assigned_to",
    )
