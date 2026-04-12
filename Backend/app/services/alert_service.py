import logging
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import Alert, AlertSeverity
from app.models.device import Device
from app.models.user import User
from app.services.alert_engine.base import AlertData
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing alerts in the database."""

    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis_client()

    def create_alert(
        self,
        device: Device,
        alert_data: AlertData,
        raw_log: dict[str, Any] | None = None,
    ) -> Alert | None:
        """
        Create an alert in the database unless a recent duplicate exists.
        
        Args:
            device: The device associated with the alert
            alert_data: The alert data structure containing type, severity, and description
            raw_log: Optional raw log details used for cache-first dedupe
            
        Returns:
            The created Alert model instance, or None if suppressed by dedupe
            
        Raises:
            ValueError: If alert data is invalid
        """
        self._validate_alert_data(alert_data)

        if self._is_duplicate_in_cache(device.id, alert_data, raw_log):
            logger.info(
                "Alert suppressed by Redis dedupe window: device_id=%s, type=%s, severity=%s",
                device.id,
                alert_data.type,
                alert_data.severity,
            )
            return None

        duplicate = self._get_recent_duplicate_alert(device.id, alert_data)
        if duplicate is not None:
            logger.info(
                "Alert suppressed by dedupe window: existing_alert_id=%s, device_id=%s, type=%s, severity=%s",
                duplicate.id,
                device.id,
                alert_data.type,
                alert_data.severity,
            )
            return None

        alert = Alert(
            device_id=device.id,
            type=alert_data.type,
            severity=alert_data.severity,
            description=alert_data.description,
            raw_log=json.dumps(raw_log, default=str) if raw_log else None,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Alert persisted: alert_id=%s, device_id=%s, type=%s, severity=%s",
            alert.id,
            alert.device_id,
            alert.type,
            alert.severity,
        )

        return alert

    def _is_duplicate_in_cache(
        self,
        device_id: int,
        alert_data: AlertData,
        raw_log: dict[str, Any] | None,
    ) -> bool:
        dedupe_seconds = settings.alert_dedupe_window_seconds
        if dedupe_seconds <= 0:
            return False

        key = self._build_cache_dedupe_key(device_id, alert_data, raw_log)
        value = self._build_cache_dedupe_value(device_id, alert_data, raw_log)

        try:
            created = self.redis.set(key, value, ex=dedupe_seconds, nx=True)
            return not bool(created)
        except Exception:
            logger.exception("Redis dedupe check failed; falling back to DB dedupe")
            return False

    def _build_cache_dedupe_key(
        self,
        device_id: int,
        alert_data: AlertData,
        raw_log: dict[str, Any] | None,
    ) -> str:
        raw_message = ""
        if raw_log:
            raw_message = str(raw_log.get("message", ""))
        fingerprint_source = "|".join(
            [
                str(device_id),
                alert_data.type,
                alert_data.severity,
                raw_message,
                alert_data.description,
            ]
        )
        digest = sha256(fingerprint_source.encode("utf-8")).hexdigest()
        return f"alerts:dedupe:{digest}"

    def _build_cache_dedupe_value(
        self,
        device_id: int,
        alert_data: AlertData,
        raw_log: dict[str, Any] | None,
    ) -> str:
        payload = {
            "device_id": device_id,
            "type": alert_data.type,
            "severity": alert_data.severity,
            "description": alert_data.description,
            "raw_log": raw_log or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return json.dumps(payload, default=str)

    def _get_recent_duplicate_alert(self, device_id: int, alert_data: AlertData) -> Alert | None:
        dedupe_seconds = settings.alert_dedupe_window_seconds
        if dedupe_seconds <= 0:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=dedupe_seconds)
        candidate = self.db.scalar(
            select(Alert)
            .where(
                Alert.device_id == device_id,
                Alert.type == alert_data.type,
                Alert.severity == alert_data.severity,
                Alert.created_at >= cutoff,
            )
            .order_by(desc(Alert.created_at))
            .limit(1)
        )

        if candidate is None:
            return None

        # Exact match on description; different IPs/timestamps = different alerts
        if candidate.description == alert_data.description:
            return candidate

        return None

    def get_alerts(
        self,
        user: User,
        page: int,
        limit: int,
        severity: str | None = None,
        device_id: int | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[dict], int]:
        user_device_ids = list(self.db.scalars(select(Device.id).where(Device.user_id == user.id)))
        if not user_device_ids:
            return [], 0

        if device_id is not None:
            if device_id not in user_device_ids:
                return [], 0
            scoped_device_ids = [device_id]
        else:
            scoped_device_ids = user_device_ids

        query = (
            select(
                Alert.id,
                Alert.device_id,
                Alert.type,
                Alert.severity,
                Alert.description,
                Alert.created_at,
            )
            .where(Alert.device_id.in_(scoped_device_ids))
        )

        if severity:
            if severity not in AlertSeverity.VALID_LEVELS:
                raise ValueError("Invalid severity value")
            query = query.where(Alert.severity == severity)

        if from_time:
            query = query.where(Alert.created_at >= from_time)

        if to_time:
            query = query.where(Alert.created_at <= to_time)

        if search:
            keyword = search.strip()
            if keyword:
                query = query.where(Alert.description.ilike(f"%{keyword}%"))

        sort_columns = {
            "id": Alert.id,
            "device_id": Alert.device_id,
            "type": Alert.type,
            "severity": Alert.severity,
            "created_at": Alert.created_at,
        }
        sort_column = sort_columns.get(sort_by)
        if sort_column is None:
            raise ValueError("Invalid sort_by value")

        if order not in {"asc", "desc"}:
            raise ValueError("Invalid order value")

        sort_expression = asc(sort_column) if order == "asc" else desc(sort_column)

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        if total == 0:
            return [], 0

        paged_query = query.order_by(sort_expression).offset((page - 1) * limit).limit(limit)
        rows = self.db.execute(paged_query).mappings().all()
        return [dict(row) for row in rows], total

    def get_alert_by_id_for_user(self, user: User, alert_id: int) -> dict | None:
        row = (
            self.db.execute(
                select(
                    Alert.id,
                    Alert.device_id,
                    Alert.type,
                    Alert.severity,
                    Alert.description,
                    Alert.created_at,
                )
                .join(Device, Device.id == Alert.device_id)
                .where(Alert.id == alert_id, Device.user_id == user.id)
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    @staticmethod
    def _validate_alert_data(alert_data: AlertData) -> None:
        """
        Validate alert data.
        
        Args:
            alert_data: The alert data to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not alert_data.type or not isinstance(alert_data.type, str):
            raise ValueError("Alert type must be a non-empty string")

        if alert_data.severity not in AlertSeverity.VALID_LEVELS:
            raise ValueError(
                f"Invalid severity: {alert_data.severity}. "
                f"Must be one of {AlertSeverity.VALID_LEVELS}"
            )

        if not alert_data.description or not isinstance(alert_data.description, str):
            raise ValueError("Alert description must be a non-empty string")
