"""
STT Processor — ROOTAI
=======================
Orchestrates STT for ROOTAI (LEO).

ROOTAI STT behavior:
- Summarizes voice notes from Abhishek
- Command extraction for infrastructure operations
- Works with Telegram voice notes
- Cleans up temp files after transcription
- Supports infra reasoning via voice input

This is ROOTAI-specific. For VSustainAI, use the separate
processor in the VSustainAI workspace.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from .stt_client import transcribe_with_retry, validate_file, STT_API_URL
from .temp_audio_manager import TempAudioManager

logger = logging.getLogger(__name__)

# ROOTAI voice processing config
ROOTAI_STT_CONFIG = {
    "api_url": STT_API_URL,
    "timeout_seconds": 60,
    "max_retries": 2,
    "auto_cleanup": True,
    "supported_formats": ["ogg", "mp3", "wav", "m4a", "opus"],
}


class ROOTAI_STT_Processor:
    """
    ROOTAI STT processor — handles voice input for LEO.

    Responsibilities:
    - Receive voice note path
    - Transcribe via shared STT API
    - Extract commands/intents for infra operations
    - Handle cleanup
    - Format transcript for agent context
    """

    def __init__(
        self,
        temp_manager: Optional[TempAudioManager] = None,
        auto_cleanup: bool = True,
    ):
        self.temp_manager = temp_manager or TempAudioManager()
        self.auto_cleanup = auto_cleanup

    def process_voice_note(
        self,
        file_path: str,
        inject_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a voice note: validate -> transcribe -> cleanup -> return.

        Args:
            file_path: Path to audio file (ogg, mp3, wav, m4a)
            inject_context: If True, returns structured context object

        Returns:
            {
                "success": bool,
                "text": str,              # raw transcript
                "summary": str,            # brief one-line summary
                "commands": List[str],     # extracted command patterns
                "language": str,           # detected language
                "error": str or None,
                "metadata": dict,
            }
        """
        result = {
            "success": False,
            "text": "",
            "summary": "",
            "commands": [],
            "language": "unknown",
            "error": None,
            "metadata": {},
        }

        # Validate
        validation = validate_file(file_path)
        if not validation["valid"]:
            result["error"] = validation["error"]
            return result

        try:
            # Transcribe
            logger.info(f"ROOTAI STT: transcribing {file_path}")
            stt_result = transcribe_with_retry(
                file_path,
                timeout_seconds=ROOTAI_STT_CONFIG["timeout_seconds"],
                max_retries=ROOTAI_STT_CONFIG["max_retries"],
            )

            if not stt_result["success"]:
                result["error"] = stt_result["error"]
                return result

            transcript = stt_result["text"]
            language = stt_result["language"]

            # Extract commands
            commands = self._extract_commands(transcript)

            # Generate summary
            summary = self._generate_summary(transcript)

            result = {
                "success": True,
                "text": transcript,
                "summary": summary,
                "commands": commands,
                "language": language,
                "error": None,
                "metadata": {
                    "file_size_mb": stt_result["metadata"].get("file_size_mb", 0),
                    "retries": stt_result["metadata"].get("retries", 0),
                    "agent": "ROOTAI",
                },
            }

            logger.info(f"ROOTAI STT success: '{transcript[:80]}...'")

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"ROOTAI STT failure: {e}")

        finally:
            # Cleanup temp file
            if self.auto_cleanup:
                self.temp_manager.cleanup(file_path)

        return result

    def process_telegram_voice(
        self,
        telegram_file_path: str,
        save_to_temp: bool = True,
    ) -> Dict[str, Any]:
        """
        Process voice note from Telegram DM.

        Telegram sends .ogg voice notes. This:
        1. Optionally copies to temp location
        2. Transcribes
        3. Cleans up
        4. Returns structured result

        Args:
            telegram_file_path: Path to Telegram voice file in media inbox
            save_to_temp: If True, copy to temp before processing

        Returns:
            Structured result (same as process_voice_note)
        """
        input_path = telegram_file_path

        if save_to_temp:
            input_path = self.temp_manager.save_temp_from_existing(
                telegram_file_path,
                copy=True,
            )

        return self.process_voice_note(input_path, inject_context=True)

    def _extract_commands(self, transcript: str) -> list:
        """
        Extract infrastructure command patterns from transcript.

        ROOTAI-specific command patterns for LEO operations.
        """
        command_patterns = [
            r"check\s+(?:the\s+)?(?:system|host|docker|container)s?",
            r"list\s+(?:all\s+)?containers?",
            r"show\s+(?:me\s+)?(?:logs|status|health)",
            r"restart\s+(?:the\s+)?(?:gateway|agent|container)",
            r"deploy\s+(?:the\s+)?(?:vss|vsustain)\s*agent",
            r"check\s+(?:the\s+)?(?:vss|vsustain)\s+agent",
            r"run\s+(?:a\s+)?(?:system\s+)?audit",
            r"show\s+(?:me\s+)?memory",
            r"update\s+(?:the\s+)?memory",
            r"push\s+(?:to\s+)?github",
            r"pull\s+(?:from\s+)?github",
            r"docker\s+(?:ps|logs|exec)",
            r"create\s+(?:a\s+)?cron\s+job",
            r"send\s+(?:a\s+)?(?:whatsapp|double ?tick)\s+message",
        ]

        commands = []
        transcript_lower = transcript.lower()

        for pattern in command_patterns:
            if re.search(pattern, transcript_lower):
                commands.append(re.search(pattern, transcript_lower).group(0))

        return list(set(commands))  # dedupe

    def _generate_summary(self, transcript: str, max_length: int = 100) -> str:
        """Generate brief one-line summary of transcript."""
        if not transcript:
            return ""

        transcript = transcript.strip()

        # Truncate if too long
        if len(transcript) <= max_length:
            return transcript

        # Try to break at a sentence boundary
        truncated = transcript[:max_length]
        last_space = truncated.rfind(" ")
        last_period = truncated.rfind(".")

        breakpoint = max(last_space, last_period)
        if breakpoint > max_length * 0.5:
            return transcript[: breakpoint + 1]

        return truncated + "..."

    def batch_process(self, file_paths: list) -> Dict[str, Any]:
        """
        Process multiple voice notes in sequence.

        Returns:
            {
                "total": int,
                "successful": int,
                "failed": int,
                "results": [...]
            }
        """
        results = []
        successful = 0
        failed = 0

        for path in file_paths:
            result = self.process_voice_note(path)
            results.append(result)
            if result["success"]:
                successful += 1
            else:
                failed += 1

        return {
            "total": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results,
        }


def process_voice_input(
    file_path: str,
    agent_type: str = "ROOTAI",
) -> Dict[str, Any]:
    """
    Convenience function for one-shot voice processing.

    Usage:
        result = process_voice_input("/tmp/voice.ogg", "ROOTAI")
    """
    if agent_type == "ROOTAI":
        processor = ROOTAI_STT_Processor()
        return processor.process_voice_note(file_path)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")