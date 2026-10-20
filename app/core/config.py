from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://dinsanloord@localhost:5432/documents"
    jwt_secret: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
