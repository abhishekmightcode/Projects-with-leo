# VSS Agent — Skill Reference

**VSS = V Sustain Solar Solutions**  
**Owner:** Pravesh Tiwari  
**Revenue Partner:** Abhishek (you)  
**Channel:** Telegram (`t.me/VSustainAIbot`)

---

## What the VSS agent does

Pravesh talks to the agent on Telegram. The agent:
1. Listens to what Pravesh says (customer names, instructions)
2. Searches Google Contacts for the customer's phone number
3. Sends WhatsApp messages to the customer via DoubleTick
4. Confirms to Pravesh on Telegram

---

## Quick Reference

### Contacts
- **Google Contacts** → search by name → get phone number
- Phone format: `91XXXXXXXXXX` (no `+`, no spaces)

### WhatsApp (DoubleTick)
- **Sender number:** `919900108067`
- **API Key:** stored in config, never exposed
- **24-hour rule:**
  - Customer replied → free-form text
  - Customer NOT replied → template message (utility type only)

### Templates available
| Template | Use when | Variables |
|----------|----------|-----------|
| `chat_support` | Simple text notification | 1 (e.g., customer name) |
| `invoice` | Image with text overlay | 3 (invoiceid, date, GST) |
| `invoice_pdf` | PDF document | 0 |

---

## End-to-End Flow

```
Pravesh on Telegram:
  "Send a message to Ramesh about his pending payment"

Agent:
  1. Hear "Ramesh" → extract name
  2. Search Google Contacts for "Ramesh" → get phone 919876543210
  3. Check chat window status for 919876543210
  4. Window closed → use chat_support template with variable "Ramesh"
  5. Call DoubleTick API
  6. Confirm to Pravesh: "Sent: Hi Ramesh, We are contacting you regarding your pending support request with us → 919876543210"
```

---

## Decision Tree

```
Did customer reply in last 24 hours?
├── YES → Send free-form text message
└── NO  → Send utility template (chat_support recommended)
           └── For documents/images: use invoice_pdf or invoice template
```

---

## Important Rules

1. **Phone numbers:** Always `91` + 10 digits. No `+`, no spaces.
2. **Templates:** Never leave variables empty. All 3 fields required for `invoice`.
3. **Delivery rate:** Utility templates > Marketing templates.
4. **API Key:** Never log, never repeat in full.
5. **Google Contacts:** Search before every message. If not found, ask Pravesh to confirm the name.

---

## Commands for Testing

```bash
# Test phone formatting
python3 integrations/doubletick.py

# Send a test template
python3 -c "
from integrations.doubletick import send_chat_support_template
result = send_chat_support_template('919876543210', 'Test Customer')
print(result)
"
```

---

## Files in this project

```
VSS/
├── docs/
│   └── VSS-DoubleTick-Integration.md   ← Full API reference
├── integrations/
│   └── doubletick.py                   ← DoubleTick Python SDK
├── skills/
│   └── vss-agent-skill.md             ← This file
└── config/
    └── vss-config.md                   ← Credentials & settings
```

---

**Last updated:** 2026-05-25