from __future__ import annotations

import os
from typing import Optional

# Make this module act like a package so that `from app.config.settings import ...` works
# even though this file exists. This avoids the name clash with the directory `app/config/`.
__path__ = [os.path.join(os.path.dirname(__file__), "config")]


class Settings:
    # JWT settings (read from environment with sensible defaults)
    JWT_SECRET: str = os.getenv("JWT_SECRET", os.getenv("ANALYSIS_JWT_SECRET", "devsecret_change_me"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "60"))
    REFRESH_TOKEN_EXPIRES_MIN: int = int(os.getenv("REFRESH_TOKEN_EXPIRES_MIN", str(7 * 24 * 60)))

    # Database (optional)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"


settings = Settings()
