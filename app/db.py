import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, settings

logger = logging.getLogger(__name__)

ASYNC_POSTGRES_SCHEME = "postgresql+asyncpg://"

_engine = None
_async_session_maker = None


class DatabaseConfigurationError(ValueError):
    """Raised when database configuration is missing or unsupported."""


def _validate_database_url(database_url: str) -> str:
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL must be set before initializing the database engine."
        )

    if not database_url.startswith(ASYNC_POSTGRES_SCHEME):
        raise DatabaseConfigurationError(
            f"DATABASE_URL must use the async driver scheme {ASYNC_POSTGRES_SCHEME}"
        )

    logger.info("Using async database URL for SQLAlchemy engine.")

    return database_url


def _build_database_url(config: Settings) -> str:
    if config.database_url:
        return config.database_url

    if not config.db_name or not config.db_user_name or not config.db_password:
        raise DatabaseConfigurationError(
            "DATABASE_URL or DB_NAME, DB_USER_NAME, and DB_PASSWORD must be set before initializing the database engine."
        )

    return (
        f"{ASYNC_POSTGRES_SCHEME}"
        f"{config.db_user_name}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}"
    )


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    global _engine, _async_session_maker

    if _async_session_maker is None:
        database_url = _validate_database_url(_build_database_url(settings))
        _engine = create_async_engine(database_url, echo=False)
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _async_session_maker


def get_engine():
    global _engine

    if _engine is None:
        get_async_session_maker()

    return _engine


async def check_database_connection() -> bool:
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))

    return True


async def get_db() -> AsyncSession:
    """Dependency for FastAPI endpoints to get a DB session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session
