from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.services.ai_service import AIService
from app.services.alert_service import AlertService
from app.services.device_service import DeviceService
from app.services.event_dispatcher import EventDispatcher
from app.services.log_service import LogService
from app.utils.jwt import TokenType, decode_token
from app.utils.redis_client import get_redis_client

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_redis() -> Redis:
    return get_redis_client()


def get_device_service(
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> DeviceService:
    return DeviceService(db=db, redis_client=redis_client)


def get_log_service(db: Session = Depends(get_db)) -> LogService:
    return LogService(db=db)


def get_event_dispatcher(db: Session = Depends(get_db)) -> EventDispatcher:
    return EventDispatcher(db=db)


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(db=db)


def get_ai_service(redis_client: Redis = Depends(get_redis)) -> AIService:
    return AIService(redis_client=redis_client)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise credentials_exception from exc

    if payload.get("type") != TokenType.ACCESS:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    try:
        return auth_service.get_current_user(int(user_id))
    except ValueError as exc:
        raise credentials_exception from exc
