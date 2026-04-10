from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils.jwt import TokenType, create_access_token, create_refresh_token, decode_token
from app.utils.security import hash_password, hash_refresh_token, verify_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, email: str, password: str) -> User:
        existing_user = self.db.scalar(select(User).where(User.email == email))
        if existing_user:
            raise ValueError("Email already registered")

        user = User(email=email, password_hash=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login_user(self, email: str, password: str) -> tuple[str, str]:
        user = self.db.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(subject=str(user.id))
        refresh_token, refresh_expires_at = create_refresh_token(subject=str(user.id))
        self._persist_refresh_token(user.id, refresh_token, refresh_expires_at)
        return access_token, refresh_token

    def refresh_access_token(self, raw_refresh_token: str, rotate: bool = True) -> tuple[str, str | None]:
        payload = decode_token(raw_refresh_token)
        if payload.get("type") != TokenType.REFRESH:
            raise ValueError("Invalid token type")

        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if not token_record:
            raise ValueError("Refresh token not found")

        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            self.db.delete(token_record)
            self.db.commit()
            raise ValueError("Refresh token expired")

        access_token = create_access_token(subject=str(token_record.user_id))

        if not rotate:
            return access_token, None

        new_refresh_token, new_expires_at = create_refresh_token(subject=str(token_record.user_id))
        self.db.delete(token_record)
        self.db.flush()
        self._persist_refresh_token(token_record.user_id, new_refresh_token, new_expires_at, commit=False)
        self.db.commit()
        return access_token, new_refresh_token

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if token_record:
            self.db.delete(token_record)
            self.db.commit()

    def get_current_user(self, user_id: int) -> User:
        user = self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise ValueError("User not found")
        return user

    def _persist_refresh_token(
        self,
        user_id: int,
        raw_refresh_token: str,
        expires_at: datetime,
        commit: bool = True,
    ) -> None:
        token_record = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=expires_at,
        )
        self.db.add(token_record)
        if commit:
            self.db.commit()
