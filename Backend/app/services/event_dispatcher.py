import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.log import Log
from app.services.alert_engine import AlertData, get_alert_engine
from app.services.alert_service import AlertService
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Internal event dispatcher for handling log events.
    
    Responsibilities:
    - Call alert engine for detection
    - Store alerts in database
    - Coordinate multiple event handlers (extensible)
    
    Design: This is isolated from the route layer, making it easy
    to replace with Kafka producer later.
    """

    def __init__(self, db: Session):
        self.db = db
        self.alert_service = AlertService(db)

    def handle_log_event(self, log: Log) -> dict:
        """
        Handle a log event by running detection and storing results.
        
        Args:
            log: The log that was just created
            
        Returns:
            Event context dictionary with processing results
        """
        event_context = {
            "log_id": log.id,
            "device_id": log.device_id,
            "device_type": log.device.device_type,
            "alerts_generated": [],
        }

        # Run alert detection
        try:
            self._run_alert_detection(log, event_context)
        except Exception as e:
            # Log detection failure but don't block other handlers
            event_context["alert_error"] = str(e)
            logger.exception("Alert detection failed for log_id=%s: %s", log.id, e)

        return event_context

    def _run_alert_detection(self, log: Log, event_context: dict) -> None:
        """
        Run alert detection on a log and store any generated alerts.
        
        Args:
            log: The log to analyze
            event_context: Dictionary to populate with results
        """
        # Get the appropriate engine for this device type
        engine = get_alert_engine(log.device.device_type)

        # Process the log
        alert_data: AlertData | None = engine.process_log(log)

        if alert_data:
            try:
                alert = self.alert_service.create_alert(
                    log.device,
                    alert_data,
                    raw_log={
                        "log_id": log.id,
                        "device_id": log.device_id,
                        "device_type": log.device.device_type,
                        "message": log.message,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    },
                )
                if alert is None:
                    logger.info(
                        "Dispatcher suppressed duplicate alert for log_id=%s, device_id=%s, type=%s, severity=%s",
                        log.id,
                        log.device_id,
                        alert_data.type,
                        alert_data.severity,
                    )
                    return
                event_context["alerts_generated"].append(
                    {
                        "alert_id": alert.id,
                        "type": alert.type,
                        "severity": alert.severity,
                    }
                )
                logger.info(
                    "Alert created from dispatcher: alert_id=%s, log_id=%s, device_id=%s, type=%s, severity=%s",
                    alert.id,
                    log.id,
                    log.device_id,
                    alert.type,
                    alert.severity,
                )
                # Broadcast the new alert to all connected WebSocket clients
                self._broadcast_alert(alert)
            except ValueError as e:
                raise ValueError(f"Failed to create alert: {str(e)}")

    def _broadcast_alert(self, alert) -> None:
        """
        Broadcast a newly created alert to all connected WebSocket clients.
        
        This method is called after an alert is successfully created and stored.
        It sends the alert to all connected clients without blocking the current
        request processing flow.
        
        Args:
            alert: The Alert model instance to broadcast
        """
        message = {
            "id": alert.id,
            "device_id": alert.device_id,
            "type": alert.type,
            "severity": alert.severity,
            "description": alert.description,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        
        # Use sync broadcast to avoid blocking the current request
        ws_manager.broadcast_sync(message)
