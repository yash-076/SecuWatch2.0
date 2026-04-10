import json
import logging
import time
from typing import Any

from kafka import KafkaConsumer

from app.config import settings
from app.services.kafka_producer import ensure_topics_exist
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _bootstrap_servers() -> list[str]:
    return [server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()]


def _build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        settings.kafka_alerts_topic,
        bootstrap_servers=_bootstrap_servers(),
        group_id=f"{settings.kafka_consumer_group_prefix}-alert-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )


def _process_alert(payload: dict[str, Any]) -> None:
    ws_manager.broadcast_sync(payload)


def run() -> None:
    ensure_topics_exist()
    consumer = _build_consumer()
    logger.info("Alert consumer started and subscribed to topic '%s'", settings.kafka_alerts_topic)

    try:
        for message in consumer:
            payload = message.value
            for attempt in range(1, 4):
                try:
                    _process_alert(payload)
                    break
                except Exception as exc:
                    logger.exception(
                        "Alert consumer processing error (attempt %s/3): %s",
                        attempt,
                        exc,
                    )
                    if attempt < 3:
                        time.sleep(attempt)
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
