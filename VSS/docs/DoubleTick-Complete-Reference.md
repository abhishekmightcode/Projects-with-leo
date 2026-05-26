# DoubleTick WhatsApp API — LEO's Complete Reference

**Owner:** VSS (V Sustain Solar Solutions)  
**Author:** LEO — converted from integration code + docs  
**Date:** 2026-05-26

---

## Overview

VSS uses **DoubleTick** as the WhatsApp Business API provider. The agent sends messages to customers on behalf of VSS staff (Pravesh handles this via the VSS Telegram bot).

---

## Credentials

| Item | Value |
|------|-------|
| **API Key** | `key_RueP4Mjgc6knJLGTgRzXP7gAejGGvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn` |
| **WABA Number (sender)** | `919900108067` — country code `91` + number `9900108067` |
| **Base URL** | `https://public.doubletick.io` |
| **Auth Header** | `Authorization: <API_KEY>` |

---

## Critical Rule: Phone Number Format

**ALWAYS: `91` followed by 10 digits. NO `+` prefix. NO spaces.**

```
✅ Correct: 919876543210
❌ Wrong:   +91 9876543210
❌ Wrong:   09876543210
```

The `format_phone_number()` function in `doubletick.py` handles all variants automatically.

---

## 24-Hour Chat Window Logic

This is the most important rule in WhatsApp Business API:

```
Customer has NOT replied in last 24 hours (window CLOSED):
→ Must use TEMPLATE messages (utility templates only)

Customer HAS replied within 24 hours (window OPEN):
→ Can send FREE-FORM TEXT messages
```

Always check with `check_chat_window_status(to_phone)` before deciding message type.

### Checking Window Status

```python
from doubletick import check_chat_window_status

result = check_chat_window_status("9876543210")
# Returns: {"window_open": bool, "last_reply_at": str or None, "message": str}
```

---

## API Endpoints

### Check Chat Window Status
```
GET /whatsapp/chatwindow/status?wabaPhone=919900108067&customerPhone=919876543210
```

### Send Template Message
```
POST /whatsapp/message/template
```

### Send Free-Form Text
```
POST /whatsapp/message/text
```

---

## Sending Messages

### Option 1: Smart Send (Recommended)

Auto-selects template vs text based on window status:

```python
from doubletick import send_message

result = send_message(
    to_phone="9876543210",
    text="Hello Ramesh, following up on your inquiry",
    use_template_fallback=True,  # falls back to template if window closed
    template_name="chat_support",  # fallback template
    template_variables=["Ramesh"]  # 1 variable for chat_support
)
# Returns: {"success": bool, "method": "text"|"template", "message_id": str}
```

### Option 2: Force Template Message

Use when you know the window is closed:

```python
from doubletick import send_template_message

result = send_template_message(
    to_phone="9876543210",
    template_name="chat_support",
    template_data={"body": {"placeholders": ["Ramesh"]}}
)
```

### Option 3: Force Free-Form Text

Only works if window is open:

```python
from doubletick import send_text_message

result = send_text_message(
    to_phone="9876543210",
    text="Hi Ramesh, thanks for your reply! Let me check on that."
)
# Fails if window is closed — returns error
```

---

## Templates Available

### Template 1: `chat_support` (TEXT — 1 variable)
**Use when:** Simple text notification, follow-up, reminder

**Variables:** 1 (customer name or reference)

**Rendered output:**
```
Hi, {VARIABLE}

We are contacting you regarding your pending support request with us
```

### Template 2: `invoice` (IMAGE + 3 variables)
**Use when:** Sending image with text overlay (invoice, notification image)

**Variables:** 3 — invoiceid, Invoicedate, Gst details

**Media:** Requires a `mediaUrl` to an image in DoubleTick's storage

### Template 3: `invoice_pdf` (DOCUMENT — no variables)
**Use when:** Sending PDF documents (proposals, invoices, contracts)

**No variables needed.**

**Media:** Requires a `mediaUrl` to a PDF in DoubleTick's storage

---

## Template Senders (Python Convenience Functions)

```python
from doubletick import (
    send_chat_support_template,
    send_invoice_template,
    send_pdf_template
)

# Simple text notification
send_chat_support_template("9876543210", "Ramesh")

# Invoice with image
send_invoice_template(
    to_phone="9876543210",
    invoice_id="INV-2024-001",
    invoice_date="2024-05-26",
    gst_details="GST: 29AAAAA0000A1Z5"
)

# PDF document
send_pdf_template("9876543210", pdf_url="https://...")
```

---

## Workflow for VSS Agent (Pravesh → Agent → Customer)

```
1. Pravesh says on Telegram:
   "Send a message to Ramesh about his pending payment"

2. VSS Agent receives → extracts name "Ramesh"

3. VSS Agent searches Google Contacts → finds Ramesh's phone: 919876543210

4. VSS Agent checks chat window:
   check_chat_window_status("919876543210")
   → window_open: False (customer hasn't replied)

5. VSS Agent sends template message:
   send_chat_support_template("919876543210", "Ramesh")

6. DoubleTick delivers:
   "Hi, Ramesh. We are contacting you regarding your pending support request with us"

7. VSS Agent confirms to Pravesh on Telegram
```

---

## Decision Tree

```
Is customer phone number available?
├── NO  → Ask Pravesh to confirm customer's name/number
└── YES → Check chat window status
         │
         ├── Window OPEN (customer replied in last 24h)
         │   └── Send free-form text message
         │
         └── Window CLOSED (no reply in last 24h)
             └── Send template message:
                 ├── Simple text → chat_support (1 var)
                 ├── Invoice image → invoice (3 vars)
                 └── PDF document → invoice_pdf (0 vars)
```

---

## Python Module Location

```
/home/aiops/.openclaw/workspace/VSS/integrations/doubletick.py
```

**Functions available:**
- `format_phone_number(phone)` — formats any phone to `91XXXXXXXXXX`
- `validate_phone(phone)` — returns bool
- `check_chat_window_status(to_phone)` — returns window status dict
- `send_template_message(...)` — generic template sender
- `send_text_message(...)` — free-form text (window must be open)
- `send_message(...)` — smart sender with auto-fallback
- `send_chat_support_template(to_phone, variable)` — 1-var text
- `send_invoice_template(to_phone, invoice_id, invoice_date, gst_details)` — image+3vars
- `send_pdf_template(to_phone, pdf_url)` — PDF

---

## Test Commands

```bash
# Run format tests
python3 /home/aiops/.openclaw/workspace/VSS/integrations/doubletick.py

# Send test chat_support template
python3 -c "
import sys
sys.path.insert(0, '/home/aiops/.openclaw/workspace/VSS/integrations')
from doubletick import send_chat_support_template
result = send_chat_support_template('919900108067', 'Test Customer')
print(result)
"
```

---

## Important Notes

1. **Utility templates have better delivery than marketing templates**
2. **Never leave template variables empty** — message will fail
3. **Google Contacts lookup** is separate — the DoubleTick integration doesn't include it
4. **API key** — never log it or expose it in traces
5. **24-hour window resets** after each customer reply

---

*LEO converted this from live integration code — 2026-05-26*