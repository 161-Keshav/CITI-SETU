from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    secret: str = os.getenv("SETU_SECRET", "setu-shield-development-secret")
    scorer_available: bool = os.getenv("SETU_SCORER_AVAILABLE", "true").lower() == "true"
    hold_minutes: int = int(os.getenv("SETU_HOLD_MINUTES", "10"))
    model_version: str = "policy-demo-2026-09-30"


settings = Settings()

