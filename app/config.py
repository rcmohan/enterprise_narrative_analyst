from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = ""
    db_name: str = ""
    db_user_name: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    openai_api_key: str = ""
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
