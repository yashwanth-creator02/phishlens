"""Application settings. All values can be overridden with PHISHLENS_* environment variables
(see .env.example)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PHISHLENS_", extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./phishlens.db"
    storage_dir: Path = Path("./storage")      # raw emails (encrypt / use Supabase Storage in production)
    model_dir: Path = Path("./models")         # <model_dir>/active/ holds the serving model

    # authentication: "disabled" (local development, single dev user) or "supabase" (verify Supabase JWT)
    auth_mode: str = "disabled"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""
    dev_user_id: str = "dev-user"

    # inbound webhook protection (shared secret sent in the X-Webhook-Secret header)
    webhook_secret: str = "change-me"
    alias_domain: str = "phishlens.example"    # forwarding alias: u-<token>@alias_domain

    # admin purge endpoint (X-Admin-Token header). Empty = disabled (503).
    admin_token: str = ""

    cors_origins: str = "http://localhost:5173"

    # risk bands (provisional starting values; tune on validation data, see docs/08-ml-pipeline.md)
    band_low_max: int = 29      # score <= 29  -> LOW
    band_high_min: int = 70     # score >= 70  -> HIGH, otherwise MEDIUM

    # explanations
    top_k_reasons: int = 5
    min_reason_contribution: float = 0.05   # in the model's native additive units (see docs/09-explainability.md)

    # sender history
    min_history_messages: int = 3
    retention_days: int = 30                # raw email retention (enforced by scripts/purge_old.py)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
