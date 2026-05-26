# VSustainAI Operational Rules

## WhatsApp — USE skills/whatsapp MODULE

**CRITICAL:**
- OpenClaw has NO native WhatsApp channel configured
- Using `message action=send channel=whatsapp` WILL FAIL — it routes to Telegram which doesn't know this phone number
- **ALWAYS** use `skills.whatsapp` for WhatsApp operations

### Import from skills.whatsapp (pre-installed at /workspace/skills/whatsapp/)

**For free-form text (customer replied within 24h):**
```python
from skills.whatsapp.client import send_text
result = send_text(to_phone="919167320425", text="Your message here")
```

**For template messages (24h window closed):**
```python
from skills.whatsapp.client import send_template
result = send_template(to_phone="919167320425", template_name="chat_support", placeholders=["Ramesh"])
```

**For smart send (auto-checks window, picks method, records in CRM):**
```python
from skills.whatsapp.workflows import send_followup, send_support_message
result = send_followup(customer_identifier="Ramesh", variable="Ramesh")
result = send_support_message(customer_identifier="919167320425", message_text="Hello!")
```

### Phone Format Rule
- Format: `91XXXXXXXXXX` — NO `+` prefix, NO spaces
- Helper: `from skills.whatsapp.formatter import format_phone_number`

### Available Templates
| Template | Variables | Use When |
|----------|-----------|----------|
| `chat_support` | 1 (name) | Follow-ups, reminders |
| `invoice` | 3 (ID, date, GST) | Invoice images |
| `invoice_pdf` | 0 | PDF proposals/documents |

### CRM Memory
Every outbound is auto-recorded in CRM:
```python
from skills.whatsapp.memory import get_memory
memory = get_memory()
memory.record_outbound(phone="919167320425", method="text", message_id="msg123", success=True)
```

## STT — USE skills/stt MODULE

Voice notes are transcribed via the shared STT API:
```python
from skills.stt.processor import transcribe
result = transcribe("/tmp/voice.ogg")
print(result.text)
```

- STT endpoint: `http://host.docker.internal:9001/transcribe`
- After transcription, route transcript via `skills.whatsapp.processor.process_message()`

## Escalation
Escalate to ROOTAI (LEO) when:
- Infrastructure issue (Docker, networking, services)
- Cross-agent coordination needed
- Abhishek explicitly requests ROOTAI involvement
