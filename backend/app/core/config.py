"""
CampusFlow AI — Application configuration.

Reads all settings from environment variables (loaded from backend/.env).
No secrets are hardcoded here.
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend/ directory
load_dotenv()


def _require(var: str) -> str:
    """Read a required environment variable. Raises at startup if missing."""
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{var}' is not set. "
            f"Copy backend/.env.example to backend/.env and fill in your values."
        )
    return value


# Required settings — the application will not start without these
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = _require("GEMINI_MODEL")

# Optional settings with safe defaults
CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:5173")
