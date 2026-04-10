import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from kafka import KafkaConsumer
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models.device import Device
from app.services.kafka_producer import ensure_topics_exist

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _bootstrap_servers() -> list[str]:
    return [server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()]


def _build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        settings.kafka_heartbeat_topic,
        bootstrap_servers=_bootstrap_servers(),
        group_id=f"{settings.kafka_consumer_group_prefix}-heartbeat-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )


def _parse_timestamp(raw_timestamp: Any) -> datetime:
    if isinstance(raw_timestamp, str):
        try:
            parsed = datetime.fromisoformat(raw_timestamp)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    return datetime.now(timezone.utc)


def _process_heartbeat(payload: dict[str, Any]) -> None:
    device_id = payload.get("device_id")
    if not isinstance(device_id, int):
        logger.warning("Skipping heartbeat event with invalid device_id: %s", payload)
        return

    timestamp = _parse_timestamp(payload.get("timestamp"))

    with SessionLocal() as db:
        device = db.scalar(select(Device).where(Device.id == device_id))
        if device is None:
            logger.warning("Heartbeat received for unknown device id %s", device_id)
            return

        device.last_seen = timestamp
        db.commit()


def run() -> None:
    ensure_topics_exist()
    consumer = _build_consumer()
    logger.info("Heartbeat consumer started and subscribed to topic '%s'", settings.kafka_heartbeat_topic)

    try:
        for message in consumer:
            payload = message.value
            for attempt in range(1, 4):
                try:
                    _process_heartbeat(payload)
                    break
                except Exception as exc:
                    logger.exception(
                        "Heartbeat consumer processing error (attempt %s/3): %s",
                        attempt,
                        exc,
                    )
                    if attempt < 3:
                        time.sleep(attempt)
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
