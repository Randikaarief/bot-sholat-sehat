from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tasks.db"

    # Timezone & Localization
    TIMEZONE: str = "Asia/Jakarta"  # WIB (UTC+7)
    DEFAULT_MORNING_DIGEST_TIME: str = "07:00"

    # LMS Sync Settings
    LMS_SYNC_INTERVAL_HOURS: int = 3

    # Server / Webhook
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WEBHOOK_MODE: bool = False
    WEBHOOK_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
