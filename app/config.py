import os
from functools import lru_cache

class Settings:
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    serpapi_key: str = os.environ.get("SERPAPI_KEY", "")
    claude_model: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    max_stores: int = int(os.environ.get("MAX_STORES", "8"))

    def validate(self) -> None:
        missing = [name for name, value in [("ANTHROPIC_API_KEY", self.anthropic_api_key), ("SERPAPI_KEY", self.serpapi_key)] if not value ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()