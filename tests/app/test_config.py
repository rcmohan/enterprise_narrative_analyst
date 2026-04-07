import os
from unittest.mock import patch
from app.config import Settings

def test_config_defaults():
    # When no env variables are set, defaults should be used (if defined)
    # Since config.py may have defaults or empty strings, we verify it parses.
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(_env_file=None)
        assert settings.database_url == "" # matches the updated code
        assert settings.db_name == ""
        assert settings.db_user_name == ""
        assert settings.db_password == ""
        assert settings.db_host == "localhost"
        assert settings.db_port == 5432
        assert settings.openai_api_key == ""

def test_config_env_overrides():
    with patch.dict(os.environ, {
        "DATABASE_URL": "postgresql+asyncpg://testhost/db",
        "DB_NAME": "analyst",
        "DB_USER_NAME": "analyst",
        "DB_PASSWORD": "secret",
        "DB_HOST": "db.local",
        "DB_PORT": "5433",
        "OPENAI_API_KEY": "test-key"
    }, clear=True):
        settings = Settings(_env_file=None)
        assert settings.database_url == "postgresql+asyncpg://testhost/db"
        assert settings.db_name == "analyst"
        assert settings.db_user_name == "analyst"
        assert settings.db_password == "secret"
        assert settings.db_host == "db.local"
        assert settings.db_port == 5433
        assert settings.openai_api_key == "test-key"
