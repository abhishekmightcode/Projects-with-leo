# WhatsApp Skills — VSustainAI

Production-grade modular WhatsApp capability framework for VSustainAI ☀️.

**Consumes:** Shared STT infrastructure + DoubleTick WhatsApp Business API  
**Role:** VSustainAI uses these capabilities — it does NOT implement raw API logic

---

## Architecture

```
Pravesh (Telegram)
    │
    ▼
VSustainAI Agent
    │ (voice or text)
    ├── STT (voice notes) → transcript
    │
    ├── processor.py — intent routing
    │   └── workflows.py — business logic
    │       ├── chat_window.py — 24h window check
    │       ├── contacts.py — customer resolution
    │       ├── memory.py — CRM state
    │       └── client.py — DoubleTick API calls
    │
    └── WhatsApp → Customer
```

---

## File Structure

```
skills/whatsapp/
├── __init__.py         — Package exports, version
├── config.py           — Environment variables (NO hardcoded secrets)
├── exceptions.py       — Custom exception hierarchy
├── formatter.py        — Phone formatting, payload validation
├── client.py           — Raw DoubleTick API client (low-level)
├── templates.py        — Template definitions + validation
├── chat_window.py     — 24-hour window logic + caching
├── contacts.py         — Google Contacts lookup (stub, replace for prod)
├── memory.py           — CRM customer state (Redis + in-memory)
├── workflows.py        — High-level business flows
├── processor.py        — Intent routing + entity extraction
├── stt_integration.py  — Voice → STT → WhatsApp pipeline
└── README.md          — This file
```

---

## Quick Start

### 1. Set Environment Variables

```bash
export DOUBLETICK_API_KEY="your_key_here"
export WABA_NUMBER="919900108067"
```

### 2. Simple Send

```python
from skills.whatsapp.workflows import send_followup

result = send_followup(customer_identifier="Ramesh", variable="Ramesh")
print(result.success, result.message_id)
```

### 3. Process Voice Note

```python
from skills.whatsapp.stt_integration import process_voice_for_whatsapp

result = process_voice_for_whatsapp("/tmp/voice.ogg", customer_name="Ramesh")
print(result["success"], result["text"], result["whatsapp_result"])
```

### 4. Process Text Command

```python
from skills.whatsapp.processor import process_message

result = process_message("send a message to Ramesh about his pending payment")
print(result.success, result.message_id)
```

---

## Core Rules

### Phone Numbers
- **Always:** `91` + 10 digits — NO `+`, NO spaces
- `format_phone_number()` handles all variants automatically
- ✅ `919876543210` — Correct
- ❌ `+91 9876543210` — Wrong
- ❌ `09876543210` — Wrong

### 24-Hour Chat Window
- **Window OPEN** (customer replied in last 24h) → Free-form text ✅
- **Window CLOSED** → Must use template message ✅
- `should_use_template(phone)` — quick check
- `can_send_text(phone)` — quick check

### Templates

| Template | Type | Variables | Use When |
|----------|------|-----------|----------|
| `chat_support` | TEXT | 1 | Follow-ups, reminders |
| `invoice` | IMAGE | 3 | Invoice images (invoiceid, date, GST) |
| `invoice_pdf` | DOCUMENT | 0 | PDF proposals, contracts |

### Temp File Cleanup
- All temp audio files are auto-deleted after STT transcription
- Manual cleanup: `cleanup_temp_file(path)`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOUBLETICK_API_KEY` | **Yes** | — | DoubleTick API key |
| `WABA_NUMBER` | No | `919900108067` | Sender number |
| `DOUBLETICK_BASE_URL` | No | `https://public.doubletick.io` | API base |
| `STT_API_URL` | No | `http://host.docker.internal:9001/transcribe` | Shared STT endpoint |
| `STT_API_FALLBACK` | No | `http://localhost:9001/transcribe` | STT fallback |
| `REDIS_HOST` | No | None | Redis for CRM (optional) |
| `REDIS_PORT` | No | `6379` | Redis port |

---

## CRM Memory

Customer state is stored and includes:
- Name, phone, last contact time
- Lead stage (new → inquiry → qualified → proposal → negotiation → closed)
- Pending actions queue
- Message history (last 50)
- Tags and notes

### Lead Stages
```
new → inquiry → qualified → proposal → negotiation → closed_won / closed_lost
```

### Workflow Example
```python
from skills.whatsapp.memory import get_memory

memory = get_memory()
memory.record_outbound(
    phone="919876543210",
    method="template",
    template_name="chat_support",
    message_id="msg123",
    placeholders=["Ramesh"],
    success=True,
    name="Ramesh",
)

state = memory.get_customer_state("919876543210")
print(state.lead_stage)  # "inquiry"
```

---

## Module Reference

### `config.py`
```python
from skills.whatsapp.config import DOUBLETICK_API_KEY, WABA_NUMBER, validate_config
validate_config()  # Check required env vars
```

### `client.py` — Raw API (low-level)
```python
from skills.whatsapp.client import DoubleTickClient, send_template, send_text
client = DoubleTickClient()
client.send_template(to_phone="919876543210", template_name="chat_support", placeholders=["Ramesh"])
```

### `chat_window.py` — Window logic
```python
from skills.whatsapp.chat_window import should_use_template, can_send_text
should_use_template("919876543210")  # True = use template, False = free text OK
```

### `templates.py` — Template management
```python
from skills.whatsapp.templates import get_template, validate_template_send
template = get_template("chat_support")
valid, err = validate_template_send("chat_support", ["Ramesh"], None)
```

### `processor.py` — Intent routing
```python
from skills.whatsapp.processor import WhatsAppProcessor
processor = WhatsAppProcessor()
result = processor.route("send a message to Ramesh about his payment")
```

### `stt_integration.py` — Voice pipeline
```python
from skills.whatsapp.stt_integration import process_voice_for_whatsapp
result = process_voice_for_whatsapp("/tmp/voice.ogg", customer_name="Ramesh")
```

### `memory.py` — CRM
```python
from skills.whatsapp.memory import get_memory, LeadStage
memory = get_memory()
memory.get_or_create("919876543210", name="Ramesh").advance_stage(LeadStage.PROPOSAL.value)
```

---

## Exception Hierarchy

```
WhatsAppError (base)
├── ConfigError
├── MissingAPIKeyError
├── InvalidPhoneError
│   └── PhoneFormatError
├── ChatWindowClosedError      # Normal — use template
├── TemplateValidationError
├── MediaValidationError
├── APIError
│   └── APITimeoutError
├── ChatWindowAPIError
├── CustomerNotFoundError
├── WorkflowError
└── CRMError
```

---

## Migration from old `doubletick.py`

Old way:
```python
from doubletick import send_chat_support_template
result = send_chat_support_template("919876543210", "Ramesh")
```

New way:
```python
from skills.whatsapp.workflows import send_followup
result = send_followup(customer_identifier="Ramesh", variable="Ramesh")
```

Or even simpler:
```python
from skills.whatsapp import send_followup
result = send_followup("Ramesh", variable="Ramesh")
```

**Key differences:**
- API key is read from env, never hardcoded
- Customer resolution by name (contacts.py)
- CRM state auto-updated (memory.py)
- Chat window auto-checked (chat_window.py)
- Intents auto-routed (processor.py)

---

## Dependencies

```
pip install requests
```

Optional (for Redis-backed CRM):
```
pip install redis
```

---

*VSustainAI ☀️ — Built for VSS (V Sustain Solar Solutions)*  
*Version 1.0.0 — 2026-05-26*