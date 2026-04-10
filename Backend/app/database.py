from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
    from psycopg2 import connect
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:  # pragma: no cover
    connect = None
    ISOLATION_LEVEL_AUTOCOMMIT = None

from app.config import settings


class Base(DeclarativeBase):
    pass


def ensure_database_exists() -> None:
    """Create the target PostgreSQL database when it's missing.

    This is intended for local/dev startup convenience only.
    """
    if not settings.auto_create_database:
        return

    url = make_url(settings.database_url)
    if url.drivername not in {"postgresql", "postgresql+psycopg2"}:
        return

    if connect is None or ISOLATION_LEVEL_AUTOCOMMIT is None:
        return

    db_name = url.database
    if not db_name:
        return

    # Connect to a maintenance database first, then create the target database.
    admin_conn = connect(
        dbname="postgres",
        user=url.username,
        password=url.password,
        host=url.host or "localhost",
        port=url.port or 5432,
    )
    try:
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None
            if not exists:
                safe_db_name = db_name.replace('"', '""')
                cur.execute(f'CREATE DATABASE "{safe_db_name}"')
    finally:
        admin_conn.close()


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
