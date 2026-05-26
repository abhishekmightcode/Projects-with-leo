# VSustainAI STT Fix — Process Documentation

**Date:** 2026-05-26  
**Issue:** VSustainAI couldn't process Telegram voice notes — STT was not live  
**Fixed by:** LEO 🦁

---

## Problem

VSustainAI (`@VSustainAIbot`) received voice notes from Abhishek but:
- No transcription was generated
- Agent couldn't hear what was said
- STT was completely dead

---

## Root Cause Analysis

### What I Found

1. **Skills files were already in place** ✅
   - `/workspace/skills/stt/` existed in the container with `stt_client.py`, `processor.py`, etc.
   - But these were Python skill wrappers — **not wired into OpenClaw**

2. **OpenClaw had NO STT config** ❌
   - `tools.media.audio` was completely absent from `openclaw.json`
   - OpenClaw defaults to provider APIs (OpenAI, Groq, etc.) which aren't configured
   - No `whisper` binary was in the container
   - `host.docker.internal` resolved but **container was on wrong Docker network**

3. **Wrong Docker network** ❌
   - `vss-agent` was on `vss_default` network
   - `stt-service` was on `stt_default` network
   - They couldn't see each other — `host.docker.internal` couldn't reach STT API

### Evidence from Logs

```
Inbound message telegram:1107443153 -> @VSustainAIbot (direct, audio/ogg, 13 chars)
```

The audio/ogg arrived, but nothing happened after — no transcription, no error, just silence.

---

## Fix Steps

### Step 1 — Connect Container to STT Network

```bash
docker network connect stt_default vss-agent
```

Now both containers share `stt_default` network:
- `stt-service`: `172.25.0.2:9001`
- `vss-agent`: `172.25.0.2` (via stt_default)

### Step 2 — Verify Connectivity

```bash
# From inside vss-agent:
curl -s -X POST http://172.25.0.2:9001/transcribe -F "file=@/path/to/audio.ogg"
```

Response: `{"success":true,"text":"...","language":"en"}` ✅

### Step 3 — Create STT CLI Wrapper

Inside the container at `/usr/local/bin/stt-api`:

```bash
#!/bin/bash
FILE="$1"
if [ -z "$FILE" ]; then
  echo 'Usage: stt-api <audio_file>' >&2
  exit 1
fi
curl -s -X POST http://172.25.0.2:9001/transcribe -F "file=${FILE}"
```

Make executable:
```bash
chmod +x /usr/local/bin/stt-api
```

### Step 4 — Wire into OpenClaw Config

Add to `/root/.openclaw-vss/openclaw.json`:

```json
{
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "maxBytes": 25000000,
        "models": [
          {
            "type": "cli",
            "command": "stt-api",
            "args": ["{{MediaPath}}"],
            "timeoutSeconds": 60
          }
        ]
      }
    }
  }
}
```

This tells OpenClaw to use the `stt-api` CLI for audio transcription.

### Step 5 — Reload Config

```bash
docker restart vss-agent
```

OpenClaw reloads and picks up the new `tools.media.audio` config.

### Step 6 — Test

Send a voice note to `@VSustainAIbot` on Telegram. Agent should now transcribe it.

---

## Architecture Summary After Fix

```
Abhishek sends voice note to @VSustainAIbot (Telegram)
        │
        ▼
VSustainAI receives audio/ogg via Telegram channel
        │
        ▼
OpenClaw stores audio in: /root/.openclaw-vss/media/inbound/<uuid>.ogg
        │
        ▼
OpenClaw runs: stt-api {{MediaPath}}
        │
        ▼
stt-api curls to: http://172.25.0.2:9001/transcribe
        │
        ▼
FasterWhisper API (stt-service) returns JSON:
{"success": true, "text": "...", "language": "en"}
        │
        ▼
OpenClaw injects transcript as {{Transcript}} or [Audio] block
        │
        ▼
Agent processes the text
```

---

## Key Files Modified

| File | Change |
|------|--------|
| `/root/.openclaw-vss/openclaw.json` | Added `tools.media.audio` config |
| `/usr/local/bin/stt-api` | Created — CLI wrapper for STT API |

---

## Permanent Fix for Future Deployments

To prevent this from happening again on rebuilds:

1. **Add to Dockerfile or docker-compose entrypoint:**
   - Connect to `stt_default` network automatically
   - Copy `stt-api` script to `/usr/local/bin/`
   - Include `tools.media.audio` in the openclaw.json template

2. **Add STT network to docker-compose:**
   ```yaml
   services:
     vss-agent:
       networks:
         - stt_default
         - vss_default
   ```

3. **Pre-configured openclaw.json** should include the `tools.media.audio` section

---

## Alternative (Python pip approach — didn't work)

Tried to install `openai-whisper` inside container:
```bash
pip3 install --break-system-packages openai-whisper
```

**Failed:** Container got OOM-killed during model download (models are several GB).

**Solution used:** CLI wrapper calling external STT service instead.

---

## What Was Already Done (No Changes Needed)

- ✅ `/workspace/skills/stt/` — Python skill wrappers exist
- ✅ `host.docker.internal:9001` resolves from host
- ✅ FasterWhisper service running and healthy
- ✅ Network connectivity confirmed

---

## Lessons Learned

1. **Skills ≠ OpenClaw config** — Having skill Python files doesn't mean OpenClaw uses them. Must configure `tools.media.audio.models`

2. **Docker network isolation** — Each Docker compose project creates its own network. Services can't talk across networks without explicit `network connect`

3. **No pip in minimal containers** — Python pip is not pre-installed in the openclaw:local container image

4. **CLI wrapper is the right approach here** — Thin shell script calling STT API is more reliable than installing heavy Python packages

---

*LEO 🦁 — documented 2026-05-26*