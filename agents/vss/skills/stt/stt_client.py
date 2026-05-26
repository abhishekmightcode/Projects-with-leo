"""
STT Client — VSustainAI
==========================
VSustainAI's STT client for shared FasterWhisper API.
Identical logic to ROOTAI — different import path in agent context.

Sends audio to: http://host.docker.internal:9001/transcribe
"""

import requests
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

STT_API_URL = "http://host.docker.internal:9001/transcribe"
STT_API_URL_FALLBACK = "http://localhost:9001/transcribe"

DEFAULT_TIMEOUT_SECONDS = 60
MAX_FILE_SIZE_MB = 25
SUPPORTED_FORMATS = {"ogg", "mp3", "wav", "m4a", "opus"}


def validate_file(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        return {"valid": False, "error": f"File not found: {file_path}", "size_mb": 0}

    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        return {"valid": False, "error": f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)", "size_mb": size_mb}

    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        return {"valid": False, "error": f"Unsupported format: .{ext}", "size_mb": size_mb}

    return {"valid": True, "error": None, "size_mb": size_mb}


def transcribe_audio(
    file_path: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    use_fallback_url: bool = False,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Send audio file to shared FasterWhisper STT API.

    Returns:
        {"success": bool, "text": str, "language": str, "error": str or None, "metadata": dict}
    """
    validation = validate_file(file_path)
    if not validation["valid"]:
        return {"success": False, "text": "", "language": "unknown", "error": validation["error"], "metadata": {"validated": False}}

    api_url = STT_API_URL_FALLBACK if use_fallback_url else STT_API_URL
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                response = requests.post(api_url, files=files, timeout=timeout_seconds)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", "unknown"),
                    "error": None,
                    "metadata": {"validated": True, "file_size_mb": validation["size_mb"], "retries": attempt},
                }
            else:
                last_error = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            last_error = f"Timeout after {timeout_seconds}s"
        except requests.exceptions.ConnectionError:
            if not use_fallback_url and attempt == 0:
                use_fallback_url = True
                api_url = STT_API_URL_FALLBACK
                continue
        except Exception as e:
            last_error = str(e)[:100]
            break

        if attempt < max_retries:
            import time
            time.sleep(2 ** attempt)

    return {
        "success": False,
        "text": "",
        "language": "unknown",
        "error": f"All attempts failed. Last error: {last_error}",
        "metadata": {"validated": True, "file_size_mb": validation["size_mb"], "retries": max_retries},
    }


def transcribe_with_retry(file_path: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, max_retries: int = 3) -> Dict[str, Any]:
    return transcribe_audio(file_path, timeout_seconds=timeout_seconds, use_fallback_url=False, max_retries=max_retries)