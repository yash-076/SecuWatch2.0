from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertAIAnalysis(Base):
    __tablename__ = "alert_ai_analyses"

    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_happened: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation_steps: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
