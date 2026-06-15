from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"), env_file_encoding="utf-8", extra="ignore"
    )

    supabase_url: HttpUrl
    supabase_service_role_key: str

    sendgrid_api_key: str | None = None
    report_email_from: str | None = None
    report_email_to: str | None = None
    alert_email_to: str | None = None

    kalshi_api_base: str = "https://external-api.kalshi.com/trade-api/v2"
    kalshi_email: str | None = None
    kalshi_password: str | None = None
    kalshi_api_key_id: str | None = None
    kalshi_private_key_path: str | None = None
    kalshi_csv_path: Path | None = None

    local_timezone: str = "America/Chicago"
    default_bankroll_units: float = 100.0
    fractional_kelly: float = 0.25
    max_bet_units: float = 2.0
    max_daily_exposure_units: float = 8.0
    fixed_unit_size: float = 1.0
    sizing_strategy: str = Field(default="kelly", pattern="^(kelly|fixed)$")

    minimum_edge: float = 0.04
    minimum_confidence: float = 0.12
    require_confirmed_starters: bool = True

    model_artifact_path: Path = Path("artifacts/model.joblib")
    feature_version: str = "v1"

    @field_validator(
        "sendgrid_api_key",
        "report_email_from",
        "report_email_to",
        "alert_email_to",
        "kalshi_email",
        "kalshi_password",
        "kalshi_api_key_id",
        "kalshi_private_key_path",
        "kalshi_csv_path",
        mode="before",
    )
    @classmethod
    def blank_optional_values_are_none(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
