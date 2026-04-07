import importlib

import pytest

import app.db as db_module
from app.config import Settings


class _FakeSessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSessionMaker:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return _FakeSessionContext(self._session)


class _FakeConnectionContext:
    def __init__(self, connection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self, connection):
        self._connection = connection

    def begin(self):
        return _FakeConnectionContext(self._connection)


def _reload_db_module():
    return importlib.reload(db_module)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_db_import_does_not_create_engine(monkeypatch):
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda *args, **kwargs: pytest.fail("engine should not be created at import time"),
    )

    module = _reload_db_module()

    assert module._engine is None
    assert module._async_session_maker is None


def test_get_async_session_maker_requires_database_url(monkeypatch):
    module = _reload_db_module()
    monkeypatch.setattr(module.settings, "database_url", "")
    monkeypatch.setattr(module.settings, "db_name", "")
    monkeypatch.setattr(module.settings, "db_user_name", "")
    monkeypatch.setattr(module.settings, "db_password", "")
    monkeypatch.setattr(module, "_engine", None)
    monkeypatch.setattr(module, "_async_session_maker", None)

    with pytest.raises(module.DatabaseConfigurationError, match="DATABASE_URL|DB_NAME"):
        module.get_async_session_maker()
    print("!!!test_get_async_session_maker_requires_database_url passed")


def test_get_async_session_maker_requires_asyncpg_url(monkeypatch):
    module = _reload_db_module()
    monkeypatch.setattr(module.settings, "database_url", "postgresql://user:pass@localhost/db")
    monkeypatch.setattr(module, "_engine", None)
    monkeypatch.setattr(module, "_async_session_maker", None)

    with pytest.raises(module.DatabaseConfigurationError, match="postgresql\\+asyncpg://"):
        module.get_async_session_maker()


def test_validate_database_url_accepts_asyncpg_url_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+asyncpg://env-user:env-pass@localhost:5432/envdb\n",
        encoding="utf-8",
    )
    settings = Settings(_env_file=env_file)

    validated_url = db_module._validate_database_url(settings.database_url)

    assert validated_url == "postgresql+asyncpg://env-user:env-pass@localhost:5432/envdb"


def test_build_database_url_from_config_components():
    settings = Settings(
        _env_file=None,
        db_name="analyst",
        db_user_name="analyst",
        db_password="secret",
        db_host="localhost",
        db_port=5432,
    )

    database_url = db_module._build_database_url(settings)

    assert database_url == "postgresql+asyncpg://analyst:secret@localhost:5432/analyst"


@pytest.mark.anyio
async def test_get_async_session_maker_uses_database_url_loaded_via_config_env_file(monkeypatch, tmp_path):
    module = _reload_db_module()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_NAME=analyst\nDB_USER_NAME=analyst\nDB_PASSWORD=analyst\nDB_HOST=localhost\nDB_PORT=5432\n",
        encoding="utf-8",
    )
    config_settings = Settings(_env_file=env_file)

    monkeypatch.setattr(module, "settings", config_settings)
    monkeypatch.setattr(module, "_engine", None)
    monkeypatch.setattr(module, "_async_session_maker", None)

    session_maker = module.get_async_session_maker()
    is_connected = await module.check_database_connection()
    print("!!!test_get_async_session_maker_uses_database_url_loaded_via_config_env_file passed")
    print("!!! session_maker:", session_maker)
    print("!!! is_connected:", is_connected)

    assert session_maker is not None
    assert is_connected is True


@pytest.mark.anyio
async def test_get_db_yields_session_with_valid_async_url(monkeypatch):
    module = _reload_db_module()
    session = object()
    created_urls = []

    def fake_create_async_engine(url, **kwargs):
        created_urls.append(url)
        return object()

    def fake_async_sessionmaker(engine, **kwargs):
        return _FakeSessionMaker(session)

    monkeypatch.setattr(module.settings, "database_url", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setattr(module, "_engine", None)
    monkeypatch.setattr(module, "_async_session_maker", None)
    monkeypatch.setattr(module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(module, "async_sessionmaker", fake_async_sessionmaker)

    yielded = []
    async for db_session in module.get_db():
        yielded.append(db_session)
        break

    assert yielded == [session]
    assert created_urls == ["postgresql+asyncpg://user:pass@localhost/db"]


def test_get_async_session_maker_builds_database_url_from_config_components(monkeypatch):
    module = _reload_db_module()
    created_urls = []
    fake_session_maker = object()

    def fake_create_async_engine(url, **kwargs):
        created_urls.append(url)
        return object()

    def fake_async_sessionmaker(engine, **kwargs):
        return fake_session_maker

    monkeypatch.setattr(module.settings, "database_url", "")
    monkeypatch.setattr(module.settings, "db_name", "analyst")
    monkeypatch.setattr(module.settings, "db_user_name", "analyst")
    monkeypatch.setattr(module.settings, "db_password", "secret")
    monkeypatch.setattr(module.settings, "db_host", "localhost")
    monkeypatch.setattr(module.settings, "db_port", 5432)
    monkeypatch.setattr(module, "_engine", None)
    monkeypatch.setattr(module, "_async_session_maker", None)
    monkeypatch.setattr(module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(module, "async_sessionmaker", fake_async_sessionmaker)

    session_maker = module.get_async_session_maker()

    assert session_maker is fake_session_maker
    assert created_urls == ["postgresql+asyncpg://analyst:secret@localhost:5432/analyst"]


@pytest.mark.anyio
async def test_check_database_connection_executes_select_1(monkeypatch):
    module = _reload_db_module()
    executed = []

    class FakeConnection:
        async def execute(self, statement):
            executed.append(str(statement))

    monkeypatch.setattr(module, "_engine", _FakeEngine(FakeConnection()))

    is_connected = await module.check_database_connection()

    assert is_connected is True
    assert executed == ["SELECT 1"]


@pytest.mark.anyio
async def test_check_database_connection_propagates_query_errors(monkeypatch):
    module = _reload_db_module()

    class FakeConnection:
        async def execute(self, statement):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(module, "_engine", _FakeEngine(FakeConnection()))

    with pytest.raises(RuntimeError, match="database unavailable"):
        await module.check_database_connection()
