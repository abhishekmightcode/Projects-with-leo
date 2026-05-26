# STT Capabilities — ROOTAI

**Agent:** LEO / ROOTAI  
**STT Endpoint:** `http://host.docker.internal:9001/transcribe`  
**Date:** 2026-05-26

---

## Overview

ROOTAI uses a **centralized FasterWhisper STT service** running on the host at `http://host.docker.internal:9001/transcribe`.

**Rule:** ROOTAI must NOT install whisper/faster-whisper locally. All transcription goes through the shared API.

---

## Infrastructure

| Component | Value |
|-----------|-------|
| STT API URL | `http://host.docker.internal:9001/transcribe` |
| Fallback URL | `http://localhost:9001/transcribe` |
| Method | `POST` — multipart file upload |
| Response | JSON: `{"success": true, "text": "...", "language": "en"}` |
| Model | FasterWhisper (CPU, int8) — `small.en` |

---

## Supported Audio Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Ogg/Opus | `.ogg` | Telegram voice notes (native) |
| MP3 | `.mp3` | Most common audio format |
| WAV | `.wav` | Uncompressed audio |
| M4A | `.m4a` | AAC audio |
| Opus | `.opus` | Alternative opus extension |

**Max file size:** 25MB

---

## STT Stack in ROOTAI

```
skills/stt/
├── stt_client.py           — API client (requests library)
├── temp_audio_manager.py   — Temp file lifecycle + cleanup
├── processor.py            — ROOTAI-specific orchestration
├── STT_CAPABILITIES.md    — This file
└── __init__.py             — Package exports
```

---

## Usage — ROOTAI STT

```python
from skills.stt import ROOTAI_STT_Processor

processor = ROOTAI_STT_Processor()

result = processor.process_voice_note("/tmp/voice.ogg")

if result["success"]:
    print(f"Transcript: {result['text']}")
    print(f"Summary: {result['summary']}")
    print(f"Commands: {result['commands']}")
else:
    print(f"Error: {result['error']}")
```

---

## Process Flow

```
1. Voice note received via Telegram
2. OpenClaw stores audio in media inbox: ~/.openclaw/media/inbound/
3. ROOTAI STT Processor:
   a. Optionally copy to temp: /tmp/rootai_stt_audio/
   b. Send to STT API: POST http://host.docker.internal:9001/transcribe
   c. Receive JSON: {success, text, language}
   d. Extract commands (infra patterns)
   e. Generate summary
   f. Auto-delete temp file (TTL = 1 hour)
4. Transcript injected into agent context as {{Transcript}}
```

---

## Temp File Rules

| Setting | Value |
|---------|-------|
| Default TTL | 1 hour |
| Temp directory | `/tmp/rootai_stt_audio/` |
| Filename pattern | `stt_YYYYMMDD_HHMMSS_<uuid8>.ext` |
| Background cleanup | Every 5 minutes |
| Auto-delete after STT | Yes (configurable) |

---

## ROOTAI-Specific Behavior

**Command extraction** — ROOTAI voice notes can contain infra commands:

- "check the system" → recognized as `check system`
- "list all containers" → recognized as `list containers`
- "restart the gateway" → recognized as `restart gateway`
- "deploy the VSS agent" → recognized as `deploy vss agent`
- "run a system audit" → recognized as `run system audit`

**Summary generation** — Transcript is summarized to max 100 chars for quick context.

**Language detection** — Returns detected language code (en, hi, etc.).

---

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `File not found` | Invalid path | Check file path |
| `Unsupported format` | Wrong extension | Convert audio |
| `File too large` | >25MB | Compress audio |
| `Connection error` | STT service down | Try localhost fallback |
| `Timeout` | STT taking too long | Increase timeout, try again |

---

## For VSustainAI

VSustainAI has its **own copy** of this skill system at:
```
/home/aiops/agents/vss/skills/stt/
```

Both agents share the **same STT API endpoint** but have **different processors**:
- ROOTAI processor → infra commands, system operations
- VSustainAI processor → customer intent, CRM formatting, sales workflows

---

*LEO 🦁 — ROOTAI STT capabilities reference*