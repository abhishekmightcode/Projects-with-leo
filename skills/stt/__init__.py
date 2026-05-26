"""
ROOTAI STT Skills Package
========================
Centralized STT for ROOTAI (LEO).
Shared FasterWhisper API at: http://host.docker.internal:9001/transcribe

Usage:
    from skills.stt import ROOTAI_STT_Processor, transcribe_with_retry

    processor = ROOTAI_STT_Processor()
    result = processor.process_voice_note("/tmp/voice.ogg")
"""

from .stt_client import (
    transcribe_audio,
    transcribe_with_retry,
    validate_file,
    STT_API_URL,
    SUPPORTED_FORMATS,
)

from .temp_audio_manager import (
    TempAudioManager,
    DEFAULT_TEMP_DIR,
    DEFAULT_TTL_SECONDS,
)

from .processor import (
    ROOTAI_STT_Processor,
    process_voice_input,
    ROOTAI_STT_CONFIG,
)

__all__ = [
    # Client
    "transcribe_audio",
    "transcribe_with_retry",
    "validate_file",
    "STT_API_URL",
    "SUPPORTED_FORMATS",
    # Manager
    "TempAudioManager",
    "DEFAULT_TEMP_DIR",
    "DEFAULT_TTL_SECONDS",
    # Processor
    "ROOTAI_STT_Processor",
    "process_voice_input",
    "ROOTAI_STT_CONFIG",
]

# Module docstring
__doc__ = """
ROOTAI STT — Centralized Speech-to-Text Skills
================================================
Uses shared FasterWhisper API (http://host.docker.internal:9001/transcribe)
for all transcription. Do NOT run local Whisper inference.

Exports:
- stt_client: Core API client
- temp_audio_manager: Temp file lifecycle with auto-cleanup
- processor: ROOTAI-specific voice processing

Supports: ogg, mp3, wav, m4a, opus
Max file size: 25MB
"""