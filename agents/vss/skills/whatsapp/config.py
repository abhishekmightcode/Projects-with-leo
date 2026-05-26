"""
Config — WhatsApp Skills Configuration
======================================
Loads configuration from environment variables.
DOUBLETICK_API_KEY and WABA_NUMBER must be set in the environment.

Usage:
    from skills.whatsapp.config import DOUBLETICK_API_KEY, WABA_NUMBER
"""

import os
from typing import Optional

# ==============================================================================
# REQUIRED ENV VARS — raise error if not set
# ==============================================================================

DOUBLETICK_API_KEY: str = os.environ.get(
    "DOUBLETICK_API_KEY",
    ""
)
WABA_NUMBER: str = os.environ.get(
    "WABA_NUMBER",
    "919900108067"  # default VSS sender number
)

# ==============================================================================
# OPTIONAL ENV VARS — with defaults
# ==============================================================================

DOUBLETICK_BASE_URL: str = os.environ.get(
    "DOUBLETICK_BASE_URL",
    "https://public.doubletick.io"
)

# STT API for voice integration
STT_API_URL: str = os.environ.get(
    "STT_API_URL",
    "http://host.docker.internal:9001/transcribe"
)

STT_API_FALLBACK: str = os.environ.get(
    "STT_API_FALLBACK",
    "http://localhost:9001/transcribe"
)

# Redis for CRM memory (optional — falls back to in-memory)
REDIS_HOST: Optional[str] = os.environ.get("REDIS_HOST", None)
REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.environ.get("REDIS_DB", "0"))

# Timeouts
DEFAULT_TIMEOUT_SECONDS: int = int(os.environ.get("DEFAULT_TIMEOUT_SECONDS", "15"))
CHAT_WINDOW_TIMEOUT: int = int(os.environ.get("CHAT_WINDOW_TIMEOUT", "10"))

# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_config() -> dict:
    """
    Validate that required config is present.
    Call this at module import time or before first API call.
    """
    errors = []
    warnings = []

    if not DOUBLETICK_API_KEY:
        errors.append("DOUBLETICK_API_KEY environment variable is not set")

    if not WABA_NUMBER:
        errors.append("WABA_NUMBER environment variable is not set")
    elif not _validate_waba_number(WABA_NUMBER):
        warnings.append(f"WABA_NUMBER '{WABA_NUMBER}' may not be in 91XXXXXXXXXX format")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _validate_waba_number(number: str) -> bool:
    digits = ''.join(c for c in number if c.isdigit())
    return digits.startswith("91") and len(digits) == 12


# ==============================================================================
# CONFIG EXPORT
# ==============================================================================

__all__ = [
    "DOUBLETICK_API_KEY",
    "WABA_NUMBER",
    "DOUBLETICK_BASE_URL",
    "STT_API_URL",
    "STT_API_FALLBACK",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "DEFAULT_TIMEOUT_SECONDS",
    "CHAT_WINDOW_TIMEOUT",
    "validate_config",
]