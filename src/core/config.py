from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://orderflow:orderflow@localhost:5432/orderflow_db"
    OMNILEDGER_URL: str = "http://localhost:3027"
    PORT: int = 3027
    NODE_ENV: str = "production"


settings = Settings()