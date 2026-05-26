# STT Ecosystem — Speech-to-Text on AIforce

**System:** AIforce (aiops@AIforce)  
**Date:** 2026-05-26  
**Compiled by:** LEO 🦁

---

## Overview

OpenClaw on AIforce uses **Whisper** (OpenAI's open-source STT) as the local transcription engine for inbound Telegram voice notes. This document covers the complete flow — from user recording a voice note to the text appearing in the agent's context.

---

## System Topology

```
User records voice note
        │
        ▼
Telegram Bot receives audio (.ogg / .opus)
        │
        ▼
OpenClaw downloads audio file
        │
        ▼
Whisper CLI transcribes ──► Transcript injected as {{Transcript}}
        │                           │
        ▼                           ▼
   Text output               Agent processes as text
```

---

## STT Stack

### Whisper CLI
- **Binary:** `/home/aiops/.local/bin/whisper`
- **Type:** Python-based OpenAI Whisper
- **Install:** `pip3 install openai-whisper`
- **Models installed:**
  - `large-v3-turbo.pt` — fastest large model (~700MB)
  - `small.pt` — smaller/faster option (~75MB)
- **Cache:** `~/.cache/whisper/`
- **Default model:** `turbo` (when not specified)

### How OpenClaw Detects Whisper

When no explicit STT provider is configured, OpenClaw auto-detects in this order:

1. **Active reply model** — if the model supports audio understanding (e.g., GPT-4o, Gemini)
2. **Local CLIs** (in priority order):
   - `sherpa-onnx-offline`
   - `whisper-cli` (whisper-cpp)
   - `whisper` ← **what we use**
   - `gemini` CLI
3. **Provider APIs** (if configured): OpenAI → Groq → xAI → Deepgram → Google → SenseAudio → ElevenLabs → Mistral

On AIforce, the active setup uses **Whisper CLI** as the transcription engine.

---

## Telegram Voice Note Flow

### Step-by-Step

```
1. User records and sends voice note in Telegram
   └─ Format: Ogg/Opus (Telegram native voice format)

2. Telegram API delivers the file to OpenClaw
   └─ File stored in OpenClaw's media inbox
   └─ Available as: {{MediaPath}} or MediaPaths

3. OpenClaw checks if audio transcription is needed
   └─ Telegram voice notes are auto-detected
   └─ Scope: processed for any chat type

4. OpenClaw runs Whisper CLI
   └─ Command: whisper <file_path> --model <model> --output_format txt
   └─ Audio file: .ogg (Telegram format)
   └─ Timeout: 60 seconds (default)

5. Transcript is extracted
   └─ Replaces Body with [Audio] block
   └─ Sets {{Transcript}} variable

6. Agent receives transcript as text
   └─ Can be used for command parsing, mention detection, etc.
   └─ In groups: preflight transcription for mention detection
```

### Telegram Voice vs Audio Files

| Type | How Sent | Transcription |
|------|----------|---------------|
| **Voice note** | User holds mic button | ✅ Transcribed (auto) |
| **Audio file** | User sends music/audio | ⚠️ Processed as media understanding |

Telegram distinguishes voice notes (`sendVoice`) from audio files (`sendAudio`):
- Voice notes: `.ogg` / `.opus`, for personal speech
- Audio files: `.mp3` / `.m4a`, for music/podcasts

OpenClaw treats voice notes specially — always transcribed when detected.

---

## OpenClaw Configuration

### Relevant Config Fields

```json5
{
  tools: {
    media: {
      audio: {
        enabled: true,           // STT enabled (default: auto-detect)
        maxBytes: 20971520,     // 20MB max (skips oversize)
        maxChars: undefined,    // No limit (full transcript)
        models: [
          {
            type: "cli",
            command: "whisper",
            args: ["--model", "small", "{{MediaPath}}"],
            timeoutSeconds: 60
          }
        ]
      }
    }
  }
}
```

### Auto-Detection (Default Behavior)

On AIforce, no explicit `tools.media.audio` is configured — OpenClaw auto-detects:

```
No explicit config
    │
    ▼
Check: Active reply model supports audio?
    │ YES → use it
    │ NO
    ▼
Check: sherpa-onnx-offline on PATH?
    │ YES → use it
    │ NO
    ▼
Check: whisper-cli on PATH?
    │ YES → use it
    │ NO
    ▼
Check: whisper on PATH? ──────────────────► YES → USE WHISPER
    │ NO
    ▼
Check: gemini CLI on PATH?
    │ YES → use it
    │ NO
    ▼
Provider APIs (OpenAI, Groq, etc.)
```

Since `whisper` is at `/home/aiops/.local/bin/whisper` and is on PATH, it gets picked up automatically.

---

## Whisper CLI Reference

### Basic Usage

```bash
# Transcribe an audio file (uses default turbo model)
whisper /path/to/audio.ogg

# Specify model explicitly
whisper audio.ogg --model small

# Output specific format
whisper audio.ogg --model medium --output_format srt

# Specify language (faster, more accurate)
whisper audio.ogg --model small --language en

# Output to specific directory
whisper audio.ogg --output_dir /tmp/transcripts --output_format txt
```

### Available Models

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| `tiny` | fastest | lowest | ~1GB | Quick tests |
| `base` | fast | decent | ~1GB | Fast turnaround |
| `small` | moderate | good | ~2GB | Balanced (what we use) |
| `medium` | slow | better | ~5GB | Higher accuracy |
| `large` | slowest | best | ~10GB | Maximum accuracy |
| `turbo` | fast | good | ~6GB | OpenAI default, speed + quality |

### Supported Output Formats

- `txt` — plain text (default for OpenClaw integration)
- `vtt` — WebVTT subtitles
- `srt` — SubRip subtitles
- `tsv` — tab-separated values
- `json` — full JSON with timestamps
- `all` — all formats above

### Whisper on AIforce

```bash
# Which whisper is being used?
which whisper
# /home/aiops/.local/bin/whisper

# What version / model info?
whisper --help 2>&1 | head -10

# Installed models
ls ~/.cache/whisper/
# large-v3-turbo.pt  small.pt
```

---

## Integration with OpenClaw

### How OpenClaw Calls Whisper

When OpenClaw's auto-detection selects Whisper:

1. **Audio path:** `{{MediaPath}}` — resolves to local file path of downloaded audio
2. **Command:** `whisper <MediaPath> --model <model> --output_format txt`
3. **Output parsing:** stdout is read as plain text transcript
4. **Timeout:** 60 seconds (default), configurable via `timeoutSeconds`

### Transcript Injection

After successful transcription:

```text
Body becomes:
[Audio] — transcript available as {{Transcript}}
```

Variables available to the agent:
- `{{Transcript}}` — full transcript text
- `{{MediaPath}}` — path to original audio file
- `{{MediaType}}` — "audio/ogg"

### Group Voice Note — Mention Detection

**Special behavior in Telegram groups with `requireMention: true`:**

```
User sends voice note in group
    │
    ▼
OpenClaw runs "preflight" transcription
    │
    ▼
Checks transcript for mention patterns (@BotName)
    │
    ├── Mention found → Full reply pipeline
    └── No mention → Message processed as text-only mention detection
```

**Why this matters:**
Voice notes in groups are transcribed BEFORE checking if the bot was mentioned. This allows the bot to detect mentions spoken in the audio rather than just typed.

---

## Media Understanding Pipeline

Whisper-based STT is part of OpenClaw's broader media understanding pipeline:

```
Step 1: Collect attachments
        └─ MediaPaths, MediaUrls, MediaTypes

Step 2: Select per-capability
        └─ For audio: first audio attachment

Step 3: Choose model
        └─ Priority: reply model > Whisper CLI > provider APIs

Step 4: Run transcription
        └─ Whisper CLI: whisper <file> --model small --output_format txt
        └─ Output: plain text transcript

Step 5: On success
        └─ Body → [Audio] block
        └─ {{Transcript}} → transcript text
```

If Whisper fails (timeout, corrupt file, etc.), OpenClaw falls back to provider APIs.

---

## Files and Locations

| Item | Path |
|------|------|
| Whisper binary | `/home/aiops/.local/bin/whisper` |
| Whisper Python module | `openai-whisper 20250625` |
| Model cache | `/home/aiops/.cache/whisper/` |
| Models available | `large-v3-turbo.pt`, `small.pt` |
| OpenClaw skill | `/usr/lib/node_modules/openclaw/skills/openai-whisper/SKILL.md` |
| Audio docs | `/usr/lib/node_modules/openclaw/docs/nodes/audio.md` |
| Media docs | `/usr/lib/node_modules/openclaw/docs/tools/media-overview.md` |

---

## Related Documentation

| Document | What it covers |
|----------|---------------|
| `docs/nodes/audio.md` | Full audio/voice note handling in OpenClaw |
| `docs/tools/media-overview.md` | Media capabilities matrix (image, audio, video, TTS, STT) |
| `docs/tools/tts.md` | Text-to-speech (outbound voice) |
| `skills/openai-whisper/SKILL.md` | Whisper skill reference for agents |

---

## Key Takeaways for VSS Agent (VSustainAI)

1. **VSustainAI receives voice notes as text** — Pravesh can send voice notes on Telegram and the agent transcribes them automatically using Whisper

2. **No API key needed for STT** — Whisper runs locally on AIforce at no cost

3. **Works offline** — Whisper is a local CLI, doesn't require external API

4. **Language support** — Whisper supports 100+ languages including Hindi and English

5. **Group mention detection** — Voice notes in groups with `requireMention: true` are preflight-transcribed to detect @mentions spoken in audio

6. **Speed vs accuracy tradeoff** — `small` model is configured. For faster turnarounds use `tiny` or `base`; for higher accuracy use `medium` or `large`

---

*LEO 🦁 — compiled 2026-05-26*