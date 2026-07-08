import json
from datetime import datetime, timezone
from typing import Any

from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import Alert, AlertSeverity
from app.models.device import Device
from app.models.user import User
from app.utils.security import generate_api_key, hash_api_key, verify_api_key

ONLINE_STATUS = "ONLINE"
OFFLINE_STATUS = "OFFLINE"


def get_device_status(last_seen: datetime | None, threshold_seconds: int | None = None) -> str:
    if last_seen is None:
        return OFFLINE_STATUS

    effective_threshold = threshold_seconds or settings.heartbeat_online_threshold_seconds
    current_time = datetime.now(timezone.utc)

    # Normalize naive datetimes defensively in case timezone info is missing.
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    elapsed_seconds = (current_time - last_seen).total_seconds()
    if elapsed_seconds < effective_threshold:
        return ONLINE_STATUS
    return OFFLINE_STATUS


class DeviceService:
    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis_client = redis_client

    def create_device(self, user: User, device_name: str, device_type: str) -> tuple[Device, str]:
        normalized_device_name = device_name.strip()
        normalized_device_type = device_type.strip().lower()
        if not normalized_device_name:
            raise ValueError("Device name is required")

        if normalized_device_type not in {"linux", "windows", "web", "application"}:
            raise ValueError("Device type must be linux, windows, web, or application")

        existing_device = self.db.scalar(
            select(Device).where(
                Device.user_id == user.id,
                func.lower(func.trim(Device.device_name)) == normalized_device_name.lower(),
            )
        )
        if existing_device:
            raise ValueError("Device name already exists for this user")

        raw_api_key = generate_api_key()
        device = Device(
            user_id=user.id,
            device_name=normalized_device_name,
            device_type=normalized_device_type,
            api_key_hash=hash_api_key(raw_api_key),
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        self._cache_device_auth_data(device, raw_api_key=raw_api_key)
        return device, raw_api_key

    def list_user_devices(self, user: User) -> list[Device]:
        stmt = (
            select(Device)
            .where(Device.user_id == user.id)
            .order_by(Device.id.desc())
        )
        return list(self.db.scalars(stmt))

    def get_devices_with_insights(self, user: User) -> list[dict[str, Any]]:
        devices_stmt = (
            select(Device)
            .where(Device.user_id == user.id)
            .order_by(Device.id.desc())
        )
        devices = list(self.db.scalars(devices_stmt))

        if not devices:
            return []

        alerts_stmt = (
            select(
                Alert.device_id,
                Alert.severity,
                func.count(Alert.id).label("count"),
            )
            .join(Device, Device.id == Alert.device_id)
            .where(Device.user_id == user.id)
            .group_by(Alert.device_id, Alert.severity)
        )
        aggregated_alerts = self.db.execute(alerts_stmt).all()

        alerts_by_device: dict[int, dict[str, int]] = {
            device.id: {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
            for device in devices
        }

        for device_id, severity, count in aggregated_alerts:
            if device_id not in alerts_by_device:
                continue

            severity_upper = (severity or "").upper()
            alerts_by_device[device_id]["total"] += count

            if severity_upper == AlertSeverity.CRITICAL:
                alerts_by_device[device_id]["critical"] += count
            elif severity_upper == AlertSeverity.HIGH:
                alerts_by_device[device_id]["high"] += count
            elif severity_upper == AlertSeverity.MEDIUM:
                alerts_by_device[device_id]["medium"] += count
            elif severity_upper == AlertSeverity.LOW:
                alerts_by_device[device_id]["low"] += count

        return [
            {
                "id": device.id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "api_key": self._get_cached_api_key(device.id),
                "ip_address": device.ip_address,
                "last_seen": device.last_seen,
                "status": get_device_status(device.last_seen),
                "alerts_summary": alerts_by_device[device.id],
                "heartbeat_interval": device.heartbeat_interval,
                "log_min_interval": device.log_min_interval,
                "log_max_interval": device.log_max_interval,
                "alert_config": device.alert_config,
            }
            for device in devices
        ]

    def authenticate_device(self, device_id: int, api_key: str) -> Device:
        cache_key = self._cache_key(device_id)
        cached_payload = self.redis_client.get(cache_key)

        if isinstance(cached_payload, str):
            cache_data: dict[str, Any] = json.loads(cached_payload)
            api_key_hash = cache_data.get("api_key_hash")
            if api_key_hash and verify_api_key(api_key, api_key_hash):
                device = self.db.scalar(select(Device).where(Device.id == device_id))
                if not device:
                    self.invalidate_device_cache(device_id)
                    raise ValueError("Device not found")
                self._cache_device_auth_data(device, raw_api_key=api_key)
                return device

            raise ValueError("Invalid device credentials")

        device = self.db.scalar(select(Device).where(Device.id == device_id))
        if not device:
            raise ValueError("Device not found")

        if not verify_api_key(api_key, device.api_key_hash):
            raise ValueError("Invalid device credentials")

        self._cache_device_auth_data(device, raw_api_key=api_key)
        return device

    def update_device_last_seen(self, device: Device, ip_address: str | None = None) -> Device:
        device.last_seen = datetime.now(timezone.utc)
        if ip_address:
            device.ip_address = ip_address
        self.db.commit()
        self.db.refresh(device)
        return device

    def delete_device(self, user: User, device_id: int) -> Device:
        device = self.db.scalar(select(Device).where(Device.id == device_id, Device.user_id == user.id))
        if not device:
            raise ValueError("Device not found")

        self.db.delete(device)
        self.db.commit()
        self.invalidate_device_cache(device_id)
        return device

    def get_device_by_id_for_user(self, user: User, device_id: int) -> Device:
        device = self.db.scalar(select(Device).where(Device.id == device_id, Device.user_id == user.id))
        if not device:
            raise ValueError("Device not found")
        return device

    def update_device_config(
        self,
        user: User,
        device_id: int,
        heartbeat_interval: int | None,
        log_min_interval: int | None,
        log_max_interval: int | None,
        alert_config: str | None,
    ) -> Device:
        device = self.get_device_by_id_for_user(user, device_id)

        if heartbeat_interval is not None:
            device.heartbeat_interval = heartbeat_interval
        if log_min_interval is not None:
            device.log_min_interval = log_min_interval
        if log_max_interval is not None:
            device.log_max_interval = log_max_interval
        if alert_config is not None:
            device.alert_config = alert_config

        self.db.commit()
        self.db.refresh(device)
        self.invalidate_device_cache(device.id)
        return device

    def invalidate_device_cache(self, device_id: int) -> None:
        self.redis_client.delete(self._cache_key(device_id))

    def _cache_key(self, device_id: int) -> str:
        return f"device:{device_id}"

    def _cache_device_auth_data(self, device: Device, raw_api_key: str | None = None) -> None:
        payload = {
            "api_key_hash": device.api_key_hash,
            "user_id": device.user_id,
        }
        if raw_api_key:
            payload["api_key"] = raw_api_key
        self.redis_client.setex(
            self._cache_key(device.id),
            settings.device_cache_ttl_seconds,
            json.dumps(payload),
        )

    def _get_cached_api_key(self, device_id: int) -> str | None:
        try:
            cached_payload = self.redis_client.get(self._cache_key(device_id))
        except Exception:
            return None

        if not isinstance(cached_payload, str):
            return None

        try:
            cache_data: dict[str, Any] = json.loads(cached_payload)
        except (TypeError, ValueError):
            return None

        api_key = cache_data.get("api_key")
        return api_key if isinstance(api_key, str) and api_key else None

