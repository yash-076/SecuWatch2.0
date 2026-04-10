import json
import logging
import threading
from datetime import datetime
from typing import Any

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, NoBrokersAvailable, TopicAlreadyExistsError

from app.config import settings

logger = logging.getLogger(__name__)

_producer: KafkaProducer | None = None
_producer_lock = threading.Lock()


def _bootstrap_servers() -> list[str]:
    return [server.strip() for server in settings.kafka_bootstrap_servers.split(",") if server.strip()]


def _json_default_serializer(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=_bootstrap_servers(),
        client_id=settings.kafka_client_id,
        value_serializer=lambda payload: json.dumps(payload, default=_json_default_serializer).encode("utf-8"),
        retries=settings.kafka_producer_retries,
        acks="all",
        request_timeout_ms=settings.kafka_producer_request_timeout_ms,
    )


def get_kafka_producer() -> KafkaProducer:
    global _producer
    if _producer is not None:
        return _producer

    with _producer_lock:
        if _producer is None:
            _producer = _build_producer()
    return _producer


def ensure_topics_exist() -> None:
    topic_names = [
        settings.kafka_logs_topic,
        settings.kafka_alerts_topic,
        settings.kafka_heartbeat_topic,
    ]

    try:
        admin = KafkaAdminClient(
            bootstrap_servers=_bootstrap_servers(),
            client_id=f"{settings.kafka_client_id}-admin",
        )
    except NoBrokersAvailable as exc:
        logger.warning(f"Kafka broker unavailable during topic setup: {exc}")
        return

    try:
        for topic_name in topic_names:
            topic = NewTopic(
                name=topic_name,
                num_partitions=1,
                replication_factor=settings.kafka_replication_factor,
            )
            try:
                admin.create_topics(new_topics=[topic], validate_only=False)
                logger.info(f"Created Kafka topic '{topic_name}'")
            except TopicAlreadyExistsError:
                logger.debug(f"Kafka topic '{topic_name}' already exists")
            except KafkaError as exc:
                logger.warning(f"Kafka topic '{topic_name}' setup skipped: {exc}")
    finally:
        admin.close()


def _produce_event(topic: str, payload: dict[str, Any], key: str | None = None) -> bool:
    for attempt in range(1, settings.kafka_producer_retries + 1):
        try:
            producer = get_kafka_producer()
            encoded_key = key.encode("utf-8") if key else None
            producer.send(topic, value=payload, key=encoded_key)
            return True
        except Exception as exc:
            logger.warning(
                "Kafka produce failed for topic '%s' (attempt %s/%s): %s",
                topic,
                attempt,
                settings.kafka_producer_retries,
                exc,
            )

    return False


def produce_log_event(log_data: dict[str, Any]) -> bool:
    return _produce_event(
        topic=settings.kafka_logs_topic,
        payload=log_data,
        key=str(log_data.get("device_id", "")),
    )


def produce_heartbeat_event(data: dict[str, Any]) -> bool:
    return _produce_event(
        topic=settings.kafka_heartbeat_topic,
        payload=data,
        key=str(data.get("device_id", "")),
    )


def produce_alert_event(alert_data: dict[str, Any]) -> bool:
    return _produce_event(
        topic=settings.kafka_alerts_topic,
        payload=alert_data,
        key=str(alert_data.get("device_id", "")),
    )
