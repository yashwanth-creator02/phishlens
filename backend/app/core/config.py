"""Application settings. All values can be overridden with PHISHLENS_* environment variables
(see .env.example)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The alias domain that ships as the default. It is not a real mailbox: its MX records do not
# point anywhere, so no provider can deliver mail to it. Anything equal to it means inbound
# forwarding is not set up, whatever the rest of the configuration says.
ALIAS_DOMAIN_PLACEHOLDER = "phishlens.example"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PHISHLENS_", extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./phishlens.db"
    storage_dir: Path = Path("./storage")      # raw emails (encrypt / use Supabase Storage in production)
    model_dir: Path = Path("./models")         # <model_dir>/active/ holds the serving model

    # authentication: "supabase" (verify Supabase JWT) or "disabled" (single-user bypass)
    auth_mode: str = "supabase"
    # The three values below are PUBLIC and belong to this project's Supabase instance.
    # The anon key is a client-side key by design - Supabase ships it in every browser
    # bundle and it grants only what the `anon` role may do, which here is nothing:
    # no table in supabase/migrations/ grants the anon role. The JWKS URL is a public
    # key endpoint. The service_role key is a SECRET: it must never be committed,
    # logged, or sent to the browser, and it is not needed here.
    supabase_url: str = "https://vmbtdrmevlovvvfvtqmd.supabase.co"
    supabase_anon_key: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtYnRkcm1ldmxvdnZ2"
        "ZnZ0cW1kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMxMTMyNDYsImV4cCI6MjEwODY4OTI0Nn0."
        "KzuP3Lnud5iphPHslZTv4oTC-Fw8-djo9HfUlG7o_80"
    )
    supabase_jwks_url: str = "https://vmbtdrmevlovvvfvtqmd.supabase.co/auth/v1/.well-known/jwks.json"
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "raw_emails"
    dev_user_id: str = "dev-user"

    # inbound webhook protection (shared secret sent in the X-Webhook-Secret header)
    webhook_secret: str = "change-me"
    alias_domain: str = ALIAS_DOMAIN_PLACEHOLDER    # forwarding alias: u-<token>@alias_domain

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
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # Starlette mirrors any origin when "*" meets allow_credentials, which is worse than it looks.
        if "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins; '*' cannot be combined with credentials")
        return origins

    @property
    def supabase_api_base(self) -> str:
        """Base URL for Supabase API calls.

        Derived from the JWKS URL when it is not set explicitly, so a deployment
        that already publishes its keys needs no extra configuration.
        """
        if self.supabase_url:
            return self.supabase_url.rstrip("/")
        if self.supabase_jwks_url:
            base = self.supabase_jwks_url.split("/auth/v1", 1)[0]
            if base:
                return base.rstrip("/")
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
