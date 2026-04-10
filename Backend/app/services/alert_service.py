from datetime import datetime, timezone

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity
from app.models.device import Device
from app.models.user import User
from app.services.alert_engine.base import AlertData


class AlertService:
    """Service for managing alerts in the database."""

    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, device: Device, alert_data: AlertData) -> Alert:
        """
        Create an alert in the database.
        
        Args:
            device: The device associated with the alert
            alert_data: The alert data structure containing type, severity, and description
            
        Returns:
            The created Alert model instance
            
        Raises:
            ValueError: If alert data is invalid
        """
        self._validate_alert_data(alert_data)

        alert = Alert(
            device_id=device.id,
            type=alert_data.type,
            severity=alert_data.severity,
            description=alert_data.description,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return alert

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
