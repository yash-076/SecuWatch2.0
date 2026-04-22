from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlertSeverity:
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    
    VALID_LEVELS = {LOW, MEDIUM, HIGH}


class AlertStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_device_id", "device_id"),
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_device_id_created_at", "device_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status: Mapped[AlertStatus] = mapped_column(
        SQLEnum(AlertStatus, name="alert_status", native_enum=False),
        nullable=False,
        default=AlertStatus.NEW,
    )
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_role: Mapped[str | None] = mapped_column(String(50), nullable=True, default="analyst")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    device = relationship("Device", back_populates="alerts")
    assignee = relationship("User", back_populates="assigned_alerts", foreign_keys=[assigned_to])
    activities = relationship(
        "AlertActivity",
        back_populates="alert",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
