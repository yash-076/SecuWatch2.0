from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.log import Log


class LogService:
    EVENT_LOG_RECEIVED = "LOG_RECEIVED"

    def __init__(self, db: Session):
        self.db = db

    def create_log(self, device: Device, message: str, timestamp: datetime | None) -> Log:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("message must not be empty")

        effective_timestamp = self._resolve_timestamp(timestamp)
        log = Log(
            device_id=device.id,
            message=normalized_message,
            timestamp=effective_timestamp,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        self.emit_log_received_event(log)
        return log

    def emit_log_received_event(self, log: Log) -> dict[str, str | int]:
        # This returns a normalized event envelope and acts as a Kafka integration seam.
        return {
            "type": self.EVENT_LOG_RECEIVED,
            "log_id": log.id,
            "device_id": log.device_id,
            "timestamp": log.timestamp.isoformat(),
        }

    def _resolve_timestamp(self, timestamp: datetime | None) -> datetime:
        if timestamp is None:
            return datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)