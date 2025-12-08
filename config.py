"""Centralized configuration module using Pydantic Settings.

Loads configuration from environment variables and .env file.
Environment variables take precedence over .env file values.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be configured via:
    - Environment variables (uppercase, e.g., GEMINI_API_KEY)
    - .env file in project root

    Required:
        gemini_api_key: Google Gemini API key for AI features.

    Optional:
        todoist_api_token: Todoist API token for task management.
        google_calendar_id: Google Calendar ID for events.
        google_credentials_path: Path to Google service account JSON.
        weather_lat: Latitude for weather location.
        weather_lon: Longitude for weather location.
        db_path: Path to SQLite database file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required
    gemini_api_key: str

    # Optional API tokens
    todoist_api_token: str | None = None

    # Google Calendar
    google_calendar_id: str | None = None
    google_credentials_path: str = "google_credentials.json"

    # Weather location (default: Central Park, NYC)
    weather_lat: float = 40.7890
    weather_lon: float = -73.9670

    # Database
    db_path: str = "db/jarvis.db"


# Singleton instance
settings = Settings()
