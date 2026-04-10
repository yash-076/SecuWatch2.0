from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.config import settings


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _build_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _build_token(subject=subject, token_type=TokenType.ACCESS, expires_delta=expires_delta)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    token = _build_token(subject=subject, token_type=TokenType.REFRESH, expires_delta=expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta
    return token, expires_at


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
