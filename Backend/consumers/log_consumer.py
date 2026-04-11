import json
import logging
import time
from hashlib import sha256
from typing import Any

from kafka import KafkaConsumer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import SessionLocal
from app.models.log import Log
from app.services.alert_engine import AlertData, get_alert_engine
from app.services.alert_service import AlertService
from app.services.kafka_producer import ensure_topics_exist, produce_alert_event
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

redis_client = get_redis_client()


def _bootstrap_servers() -> list[str]:
    return [server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()]


def _build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        settings.kafka_logs_topic,
        bootstrap_servers=_bootstrap_servers(),
        group_id=f"{settings.kafka_consumer_group_prefix}-log-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )


def _dedupe_key(log_id: int, alert_data: AlertData) -> str:
    raw = f"{log_id}:{alert_data.type}:{alert_data.severity}:{alert_data.description}"
    digest = sha256(raw.encode("utf-8")).hexdigest()
    return f"alerts:dedupe:{digest}"


def _is_duplicate_alert(log_id: int, alert_data: AlertData) -> bool:
    key = _dedupe_key(log_id, alert_data)
    created = redis_client.set(key, "1", ex=3600, nx=True)
    return not bool(created)


def _process_log_message(payload: dict[str, Any]) -> None:
    log_id = payload.get("log_id")
    if not isinstance(log_id, int):
        logger.warning("Skipping log event with invalid log_id: %s", payload)
        return

    with SessionLocal() as db:
        log = db.scalar(
            select(Log)
            .where(Log.id == log_id)
            .options(selectinload(Log.device))
        )
        if log is None:
            logger.warning("Log id %s not found; skipping", log_id)
            return
        if log.device is None:
            logger.warning("Log id %s has no device relation; skipping", log_id)
            return

        engine = get_alert_engine(log.device.device_type)
        alert_data = engine.process_log(log)
        if alert_data is None:
            return

        if _is_duplicate_alert(log.id, alert_data):
            logger.info("Duplicate alert suppressed for log id %s", log.id)
            return

        alert_service = AlertService(db)
        alert = alert_service.create_alert(log.device, alert_data)
        published = produce_alert_event(
            {
                "id": alert.id,
                "device_id": alert.device_id,
                "type": alert.type,
                "severity": alert.severity,
                "description": alert.description,
                "created_at": alert.created_at.isoformat(),
            }
        )
        logger.info(
            "Consumer created alert: alert_id=%s, log_id=%s, device_id=%s, type=%s, severity=%s",
            alert.id,
            log.id,
            log.device_id,
            alert.type,
            alert.severity,
        )
        if not published:
            logger.warning("Kafka alert event publish failed for alert_id=%s", alert.id)


def run() -> None:
    ensure_topics_exist()
    consumer = _build_consumer()
    logger.info("Log consumer started and subscribed to topic '%s'", settings.kafka_logs_topic)

    try:
        for message in consumer:
            payload = message.value
            for attempt in range(1, 4):
                try:
                    _process_log_message(payload)
                    break
                except Exception as exc:
                    logger.exception(
                        "Log consumer processing error (attempt %s/3): %s",
                        attempt,
                        exc,
                    )
                    if attempt < 3:
                        time.sleep(attempt)
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
