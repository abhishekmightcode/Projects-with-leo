"""
STT Client — Shared FasterWhisper API client
==============================================
Centralized STT client for both ROOTAI and VSustainAI.
Sends audio to: http://host.docker.internal:9001/transcribe

Do NOT install whisper/faster-whisper in agents.
Do NOT run local inference.
"""

import requests
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# STT API endpoint — shared service
STT_API_URL = "http://host.docker.internal:9001/transcribe"

# Fallback to localhost if host.docker.internal not reachable from host context
STT_API_URL_FALLBACK = "http://localhost:9001/transcribe"

# Configurable defaults
DEFAULT_TIMEOUT_SECONDS = 60
MAX_FILE_SIZE_MB = 25
SUPPORTED_FORMATS = {"ogg", "mp3", "wav", "m4a", "opus", "ogg"}


def validate_file(file_path: str) -> Dict[str, Any]:
    """
    Validate audio file exists and is within size limits.

    Returns: {"valid": bool, "error": str or None, "size_mb": float}
    """
    path = Path(file_path)

    if not path.exists():
        return {"valid": False, "error": f"File not found: {file_path}", "size_mb": 0}

    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "valid": False,
            "error": f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)",
            "size_mb": size_mb,
        }

    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        return {
            "valid": False,
            "error": f"Unsupported format: .{ext} (supported: {', '.join(SUPPORTED_FORMATS)})",
            "size_mb": size_mb,
        }

    return {"valid": True, "error": None, "size_mb": size_mb}


def transcribe_audio(
    file_path: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    use_fallback_url: bool = False,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Send audio file to shared FasterWhisper STT API.

    Args:
        file_path: Path to audio file (ogg, mp3, wav, m4a, opus)
        timeout_seconds: API call timeout
        use_fallback_url: Use localhost fallback instead of host.docker.internal
        max_retries: Number of retry attempts on failure

    Returns:
        {
            "success": bool,
            "text": str,           # transcript
            "language": str,       # detected language
            "error": str or None,  # error message if failed
            "metadata": dict       # extra info (file_size, retries, etc.)
        }

    Example:
        result = transcribe_audio("/tmp/audio.ogg")
        if result["success"]:
            print(f"Transcript: {result['text']}")
        else:
            print(f"Error: {result['error']}")
    """
    # Validate
    validation = validate_file(file_path)
    if not validation["valid"]:
        return {
            "success": False,
            "text": "",
            "language": "unknown",
            "error": validation["error"],
            "metadata": {"validated": False},
        }

    # Choose URL
    api_url = STT_API_URL_FALLBACK if use_fallback_url else STT_API_URL

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"STT request attempt {attempt + 1}: {file_path}")

            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                response = requests.post(
                    api_url,
                    files=files,
                    timeout=timeout_seconds,
                )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"STT success: '{data.get('text', '')[:50]}...'")

                return {
                    "success": True,
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", "unknown"),
                    "error": None,
                    "metadata": {
                        "validated": True,
                        "file_size_mb": validation["size_mb"],
                        "retries": attempt,
                        "api_url": api_url,
                    },
                }

            elif response.status_code == 413:
                return {
                    "success": False,
                    "text": "",
                    "language": "unknown",
                    "error": f"File too large for STT service (HTTP 413)",
                    "metadata": {"validated": True, "file_size_mb": validation["size_mb"]},
                }

            else:
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"STT attempt {attempt + 1} failed: {last_error}")

        except requests.exceptions.Timeout:
            last_error = f"Timeout after {timeout_seconds}s"
            logger.warning(f"STT attempt {attempt + 1} timed out")

        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)[:100]}"
            logger.warning(f"STT attempt {attempt + 1} connection error: {last_error}")

            # Try fallback URL on first connection failure
            if not use_fallback_url and attempt == 0:
                logger.info("Trying fallback localhost URL...")
                use_fallback_url = True
                api_url = STT_API_URL_FALLBACK
                continue

        except Exception as e:
            last_error = f"Unexpected error: {str(e)[:200]}"
            logger.error(f"STT attempt {attempt + 1} error: {last_error}")
            break

        # Wait before retry (exponential backoff)
        if attempt < max_retries:
            import time
            wait = 2**attempt
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    return {
        "success": False,
        "text": "",
        "language": "unknown",
        "error": f"All {max_retries + 1} attempts failed. Last error: {last_error}",
        "metadata": {
            "validated": True,
            "file_size_mb": validation["size_mb"],
            "retries": max_retries,
            "api_url": api_url,
        },
    }


def transcribe_with_retry(
    file_path: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Convenience wrapper with built-in retry logic.
    Automatically tries fallback URL once if host.docker.internal fails.
    """
    return transcribe_audio(
        file_path,
        timeout_seconds=timeout_seconds,
        use_fallback_url=False,
        max_retries=max_retries,
    )