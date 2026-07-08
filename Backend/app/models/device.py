from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, default="linux")
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_interval: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    log_min_interval: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    log_max_interval: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    alert_config: Mapped[str | None] = mapped_column(Text, nullable=True, default='{"local_detection": true, "severity_threshold": "MEDIUM"}')

    user = relationship("User", back_populates="devices")
    logs = relationship(
        "Log",
        back_populates="device",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    alerts = relationship(
        "Alert",
        back_populates="device",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
