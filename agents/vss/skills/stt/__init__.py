"""
VSustainAI STT Skills Package
==============================
Speech-to-Text skills for VSustainAI.
Shared FasterWhisper API at: http://host.docker.internal:9001/transcribe

Usage:
    from skills.stt import VSustainAI_STT_Processor, transcribe_with_retry

    processor = VSustainAI_STT_Processor()
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
    VSustainAI_STT_Processor,
    process_voice_input,
    VSUSTAINAI_STT_CONFIG,
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
    "VSustainAI_STT_Processor",
    "process_voice_input",
    "VSUSTAINAI_STT_CONFIG",
]

__doc__ = """
VSustainAI STT — Solar Operations Speech-to-Text
===================================================
Uses shared FasterWhisper API (http://host.docker.internal:9001/transcribe)
for all transcription. Do NOT run local Whisper inference.

Exports:
- stt_client: Core API client
- temp_audio_manager: Temp file lifecycle with auto-cleanup
- processor: VSustainAI-specific business voice processing

Supports: ogg, mp3, wav, m4a, opus
Max file size: 25MB
"""