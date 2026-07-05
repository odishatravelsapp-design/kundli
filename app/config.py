"""Application settings.

Everything runs free/offline by default. If an LLM API key is provided via
environment (.env), AI narratives are enabled automatically — no code change.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kundli API"
    # LLM provider: auto | anthropic | openai | gemini | ollama | none
    llm_provider: str = "auto"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    ollama_base_url: str = ""  # e.g. http://host.docker.internal:11434
    ollama_model: str = "llama3.1"

    default_tz_offset: float = 5.5  # IST

    # ---- Google auth (activates only when google_client_id is set) ----
    google_client_id: str = ""
    session_secret: str = "change-me-in-production"
    allowed_emails: str = ""        # comma-separated allowlist
    ai_daily_limit: int = 20        # per-user AI calls per day (when auth on)

    class Config:
        env_file = ".env"
        extra = "ignore"

    def resolve_provider(self) -> str:
        if self.llm_provider != "auto":
            return self.llm_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        if self.ollama_base_url:
            return "ollama"
        return "none"


@lru_cache
def get_settings() -> Settings:
    return Settings()
