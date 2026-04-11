import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_device_service, get_event_dispatcher, get_log_service
from app.schemas.log import LogIngestRequest, LogIngestResponse
from app.services.device_service import DeviceService
from app.services.event_dispatcher import EventDispatcher
from app.services.kafka_producer import produce_log_event
from app.services.log_service import LogService

router = APIRouter(tags=["Logs"])
logger = logging.getLogger(__name__)


@router.post("/logs", response_model=LogIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_log(
    payload: LogIngestRequest,
    device_service: DeviceService = Depends(get_device_service),
    event_dispatcher: EventDispatcher = Depends(get_event_dispatcher),
    log_service: LogService = Depends(get_log_service),
):
    try:
        device = device_service.authenticate_device(
            device_id=payload.device_id,
            api_key=payload.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        log = log_service.create_log(
            device=device,
            message=payload.message,
            timestamp=payload.timestamp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    logger.info(
        "Log persisted: log_id=%s, device_id=%s",
        log.id,
        log.device_id,
    )

    # Primary path: publish for async consumer-driven alert creation.
    kafka_published = produce_log_event(
        {
            "log_id": log.id,
            "device_id": log.device_id,
            "message": log.message,
            "timestamp": log.timestamp.isoformat(),
        }
    )
    if not kafka_published:
        logger.warning("Kafka log event publish failed for log_id=%s", log.id)

    # Fallback path: if Kafka is unavailable, run immediate dispatcher detection.
    if not kafka_published:
        logger.warning(
            "Kafka unavailable for log_id=%s; falling back to immediate dispatcher processing",
            log.id,
        )
        dispatch_result = event_dispatcher.handle_log_event(log)
        logger.info(
            "Fallback dispatcher processed log_id=%s: alerts_generated=%s, alert_error=%s",
            log.id,
            len(dispatch_result.get("alerts_generated", [])),
            dispatch_result.get("alert_error"),
        )

    last_seen_updated = True
    try:
        device_service.update_device_last_seen(device)
    except Exception as exc:
        # Best effort backup heartbeat update; ingestion success should not be blocked.
        last_seen_updated = False
        logger.warning("Failed to update last_seen for device_id=%s: %s", device.id, exc)

    return LogIngestResponse(
        success=True,
        log_id=log.id,
        device_id=log.device_id,
        timestamp=log.timestamp,
        event_type=LogService.EVENT_LOG_RECEIVED,
        last_seen_updated=last_seen_updated,
    )