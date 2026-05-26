"""
STT Integration — Voice Note to WhatsApp Workflow
====================================================
Bridges the shared STT infrastructure with the WhatsApp skills.

Workflow:
voice note → temp file → STT API → transcript → WhatsApp processor → WhatsApp send

Usage:
    from skills.whatsapp.stt_integration import process_voice_for_whatsapp

    result = process_voice_for_whatsapp("/tmp/voice.ogg", customer_name="Ramesh")
"""

import os
import logging
import requests
from typing import Optional, Dict, Any, Tuple

from .config import STT_API_URL, STT_API_FALLBACK
from .processor import WhatsAppProcessor, get_processor
from .workflows import WorkflowResult

logger = logging.getLogger(__name__)


# ==============================================================================
# STT CLIENT (local, inside container)
# ==============================================================================

def transcribe_audio(
    file_path: str,
    timeout_seconds: int = 60,
) -> Tuple[bool, str, str]:
    """
    Transcribe an audio file using the shared STT API.

    Args:
        file_path: Path to audio file (ogg, mp3, wav, m4a)
        timeout_seconds: Timeout for API call

    Returns:
        (success, transcript_text, language_code)
    """
    if not os.path.exists(file_path):
        return False, "", "unknown"

    # Try host.docker.internal first, fallback to localhost
    urls = [STT_API_URL, STT_API_FALLBACK]
    last_error = None

    for api_url in urls:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                response = requests.post(
                    api_url,
                    files=files,
                    timeout=timeout_seconds,
                )

            if response.status_code == 200:
                data = response.json()
                text = data.get("text", "").strip()
                language = data.get("language", "unknown")
                logger.info(f"STT success: '{text[:50]}...' lang={language}")
                return True, text, language

            last_error = f"HTTP {response.status_code}: {response.text[:100]}"

        except requests.exceptions.Timeout:
            last_error = f"Timeout after {timeout_seconds}s"
            logger.warning(f"STT timeout with {api_url}")

        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)[:80]}"
            logger.warning(f"STT connection error with {api_url}: {last_error}")

        except Exception as e:
            last_error = str(e)[:100]
            logger.error(f"STT error with {api_url}: {last_error}")

    logger.error(f"STT failed after trying all URLs. Last error: {last_error}")
    return False, "", "unknown"


def cleanup_temp_file(file_path: str) -> None:
    """Safely delete a temp audio file."""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Deleted temp audio: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")


# ==============================================================================
# VOICE → WHATSAPP PIPELINE
# ==============================================================================

def process_voice_for_whatsapp(
    audio_file_path: str,
    customer_identifier: str = None,
    cleanup: bool = True,
) -> Dict[str, Any]:
    """
    Full pipeline: transcribe voice note + send WhatsApp message.

    This is the main integration function between STT and WhatsApp.

    Args:
        audio_file_path: Path to the voice note audio file
        customer_identifier: Customer name or phone (if known from context)
        cleanup: Auto-delete the temp audio file after processing

    Returns:
        {
            "success": bool,
            "transcribed": bool,
            "text": str,            # transcript
            "language": str,
            "whatsapp_result": WorkflowResult or None,
            "error": str or None,
        }
    """
    result = {
        "success": False,
        "transcribed": False,
        "text": "",
        "language": "unknown",
        "whatsapp_result": None,
        "error": None,
    }

    try:
        # Step 1: Transcribe
        success, transcript, language = transcribe_audio(audio_file_path)
        result["transcribed"] = success
        result["text"] = transcript
        result["language"] = language

        if not success or not transcript:
            result["error"] = "Transcription failed or returned empty"
            return result

        # Step 2: Route to WhatsApp processor
        # If customer_identifier was provided, prepend it to the transcript for context
        processor = get_processor()

        if customer_identifier:
            # Customer known from context — use transcript as the message
            whatsapp_result = processor.route(
                f"send a message to {customer_identifier} about {transcript}"
            )
        else:
            # Customer unknown — route transcript as-is
            whatsapp_result = processor.route_voice_transcript(transcript)

        result["whatsapp_result"] = whatsapp_result
        result["success"] = whatsapp_result.success

        if not whatsapp_result.success:
            result["error"] = whatsapp_result.error

        return result

    except Exception as e:
        logger.error(f"process_voice_for_whatsapp failed: {e}")
        result["error"] = str(e)
        return result

    finally:
        if cleanup:
            cleanup_temp_file(audio_file_path)


def transcribe_and_route(
    audio_file_path: str,
) -> Tuple[bool, str, WorkflowResult]:
    """
    Simpler version: just transcribe and route, no auto-send.

    Use this when you want to inspect the transcript before deciding
    what action to take.

    Returns:
        (transcription_success, transcript_text, workflow_result)
    """
    success, transcript, language = transcribe_audio(audio_file_path)

    if not success or not transcript:
        return False, transcript, None

    processor = get_processor()
    workflow_result = processor.route_voice_transcript(transcript)

    return True, transcript, workflow_result


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "transcribe_audio",
    "cleanup_temp_file",
    "process_voice_for_whatsapp",
    "transcribe_and_route",
]