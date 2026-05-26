# STT Capabilities — VSustainAI

**Agent:** VSustainAI ☀️  
**STT Endpoint:** `http://host.docker.internal:9001/transcribe`  
**Workspace:** `/home/aiops/agents/vss/`  
**Date:** 2026-05-26

---

## Overview

VSustainAI uses a **centralized FasterWhisper STT service** running on the host at `http://host.docker.internal:9001/transcribe`.

**Rule:** VSustainAI must NOT install whisper/faster-whisper locally. All transcription goes through the shared API.

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

## STT Stack for VSustainAI

```
agents/vss/skills/stt/
├── stt_client.py           — Shared FasterWhisper API client
├── temp_audio_manager.py   — Temp file lifecycle + auto-cleanup
├── processor.py            — VSustainAI-specific business logic
├── STT_CAPABILITIES.md    — This file
└── __init__.py             — Package exports
```

---

## Usage — VSustainAI STT

```python
from skills.stt import VSustainAI_STT_Processor

processor = VSustainAI_STT_Processor()

result = processor.process_voice_note("/tmp/voice.ogg")

if result["success"]:
    print(f"Transcript: {result['text']}")
    print(f"Intent: {result['intent']}")
    print(f"Customer: {result['customer_name']}")
    print(f"Entities: {result['entities']}")
    print(f"WhatsApp Action: {result['whatsapp_action']}")
else:
    print(f"Error: {result['error']}")
```

---

## Process Flow

```
1. Pravesh sends voice note via Telegram → @VSustainAIbot
2. OpenClaw stores audio in container media inbox: /root/.openclaw/media/inbound/
3. VSustainAI STT Processor:
   a. Optionally copy to temp: /tmp/vsustainai_stt_audio/
   b. Send to STT API: POST http://host.docker.internal:9001/transcribe
   c. Receive JSON: {success, text, language}
   d. Extract business entities (customer name, phone, kVA, amounts)
   e. Classify intent (send_whatsapp, update_crm, price_quote, etc.)
   f. Build WhatsApp action object
   g. Auto-delete temp file (TTL = 1 hour)
4. Formatted output injected into agent context for business workflow
```

---

## Temp File Rules

| Setting | Value |
|---------|-------|
| Default TTL | 1 hour |
| Temp directory | `/tmp/vsustainai_stt_audio/` |
| Filename pattern | `vss_stt_YYYYMMDD_HHMMSS_<uuid8>.ext` |
| Background cleanup | Every 5 minutes |
| Auto-delete after STT | Yes (configurable) |

---

## VSustainAI-Specific Behavior

### Intent Classification

When Pravesh sends a voice note, VSustainAI classifies the intent:

| Intent | Trigger Words | Action |
|--------|-------------|--------|
| `send_whatsapp` | "send to...", "message to...", "whatsapp to..." | Prepare WhatsApp message |
| `update_crm` | "update crm", "add to crm", "log in crm" | Queue CRM update |
| `price_quote` | "price quote", "how much", "kVA price" | Generate price response |
| `site_visit` | "site visit", "schedule visit", "installation" | Book site visit |
| `payment` | "payment", "invoice", "due" | Trigger payment flow |
| `follow_up` | "follow up", "pending", "remind" | Schedule follow-up |
| `inquiry` | "interested", "enquiry", "want to know" | Log inquiry |
| `complaint` | "issue", "problem", "not working" | Create support ticket |

### Entity Extraction

Extracts from transcript:
- **Phone numbers:** Indian format (91XXXXXXXXXX)
- **System sizes:** kVA ratings (3kVA, 5kVA, 10kVA)
- **Amounts:** ₹ amounts
- **Dates:** Various date formats
- **Customer names:** From "send to X", "for X", "about X"

### WhatsApp Action Builder

After intent classification, builds a WhatsApp action:

```python
{
    "intent": "send_whatsapp",
    "template": "chat_support",    # or None for free-text
    "variables": ["Ramesh"],       # for template
    "free_text": None,             # or custom message
    "send": True
}
```

---

## ROOTAI vs VSustainAI — Key Differences

| Aspect | ROOTAI | VSustainAI |
|--------|--------|------------|
| **Primary use** | Infrastructure commands | Business workflows |
| **Command extraction** | Docker, deploy, cron, git | WhatsApp, CRM, sales |
| **Customer context** | System state | Solar sales, VSS operations |
| **Temp directory** | `/tmp/rootai_stt_audio/` | `/tmp/vsustainai_stt_audio/` |
| **Intent patterns** | Infra operations | Solar sales operations |

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

*VSustainAI ☀️ — VSS Speech-to-Text capabilities*