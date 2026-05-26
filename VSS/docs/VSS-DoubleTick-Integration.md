# VSS DoubleTick WhatsApp Integration

## Overview
VSS (V Sustain Solar Solutions) uses **DoubleTick** as the WhatsApp messaging provider. The agent sends messages to customers on behalf of Pravesh (VSS owner) via the VSS Telegram bot.

---

## Credentials (DO NOT expose)

- **API Key:** `key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn`
- **WABA Number (sender):** `919900108067` (country code `91` + number `9900108067`)

---

## Critical Rule: Phone Number Format

**ALWAYS use `91` followed by 10 digits. NO `+` prefix. NO spaces.**

```
✅ Correct: 919876543210
❌ Wrong: +91 9876543210
❌ Wrong: 09876543210
```

Pravesh speaks names of customers. Agent must:
1. Search Google Contacts for that name
2. Get the customer's phone number
3. Format as `91` + 10-digit number (no `+`)
4. Use in all DoubleTick API calls

---

## DoubleTick API Base

- **Base URL:** `https://public.doubletick.io`
- **Auth Header:** `Authorization: key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn`

---

## 24-Hour Chat Window Logic

```
Customer has NOT replied yet (window closed):
→ Must use TEMPLATE messages (utility templates only — high delivery rate)

Customer HAS replied within 24 hours (window open):
→ Can send FREE-FORM TEXT messages (no template needed)
```

**Rule:** Always check chat window status before deciding message type.
Use `GET /whatsapp/chatwindow/status?wabaPhone={from}&customerPhone={to}` to check.

---

## Template Reference

### Template 1: `invoice` (IMAGE + 3 variables)
Use when: Sending an image with text overlay (e.g., invoice image, notification image)

**Variables:** `invoiceid`, `Invoicedate`, `Gst details` — all 3 must be provided

**curl:**
```bash
curl --request POST \
 --url "https://public.doubletick.io/whatsapp/message/template" \
 --header 'accept: application/json' \
 --header 'content-type: application/json' \
 --header 'Authorization: key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn' \
 --data '{"messages":[{"to":"TO_NUMBER","from":"919900108067","content":{"templateName":"invoice","language":"en","templateData":{"header":{"type":"IMAGE","mediaUrl":"https://data-storage.doubletick.io/org_4NohhoUgic/templates/9c5cbff0-fcbe-4e9b-a996-dc1d93c52260.png","filename":"9c5cbff0-fcbe-4e9b-a996-dc1d93c52260.png"},"body":{"placeholders":["invoiceid","Invoicedate","Gst details"]}}}}]}'
```

**Rendered output:**
```
Hello,
{invoiceid}
{Invoicedate}
{Gst details}
Thank you for reaching out to our Customer Success team.
If you need any further information or clarification, feel free to let us know.
```

---

### Template 2: `invoice_pdf` (DOCUMENT — no variables)
Use when: Sending a PDF document (proposals, invoices, contracts)

**No variables needed.** Just provide the PDF URL.

**curl:**
```bash
curl --request POST \
 --url "https://public.doubletick.io/whatsapp/message/template" \
 --header 'accept: application/json' \
 --header 'content-type: application/json' \
 --header 'Authorization: key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn' \
 --data '{"messages":[{"to":"TO_NUMBER","from":"919900108067","content":{"templateName":"invoice_pdf","language":"en","templateData":{"header":{"type":"DOCUMENT","mediaUrl":"https://data-storage.doubletick.io/org_4NohhoUgic/templates/6c123c5d-e532-42ca-a9c0-bb96ddd8bc03.pdf","filename":"6c123c5d-e532-42ca-a9c0-bb96ddd8bc03.pdf"},"body":{"placeholders":[]}}}}]}'
```

**Rendered output:**
```
Thank you for reaching out to our Customer Success team.
As per your request, please find the proposal you had asked for attached/shared here. If you need any further information or clarification, feel free to let us know.
```

---

### Template 3: `chat_support` (TEXT — 1 variable)
Use when: Sending a simple text notification (e.g., support follow-up, appointment reminder)

**1 variable** — commonly used for customer name or reference number.

**curl:**
```bash
curl --request POST \
 --url "https://public.doubletick.io/whatsapp/message/template" \
 --header 'accept: application/json' \
 --header 'content-type: application/json' \
 --header 'Authorization: key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn' \
 --data '{"messages":[{"to":"TO_NUMBER","from":"919900108067","content":{"templateName":"chat_support","language":"en","templateData":{"body":{"placeholders":["VARIABLE_VALUE"]}}}}]}'
```

**Rendered output:**
```
Hi, {VARIABLE_VALUE}

We are contacting you regarding your pending support request with us
```

---

## Free-Form Text Messages (24-hour window open)

When customer has replied within the last 24 hours, send normal text:

**Endpoint:** `POST https://public.doubletick.io/whatsapp/message/text`

```bash
curl --request POST \
 --url "https://public.doubletick.io/whatsapp/message/text" \
 --header 'accept: application/json' \
 --header 'content-type: application/json' \
 --header 'Authorization: key_RueP4Mjgc6knJLGTgRzXP7gAejGGxvyQsgzqd7M8QCtim3oRWIBJKxnYdPUhU2h7CAF1sT52KCzM9E6RfDpk1tN5B9WHFaMcKLIq76uM4ZSrv71tYFe0A2nRTzvb0gy1vwSFr2VYysbdDOkppPmNp7QZTBEPKDf4CzFCaaXCNNojzpF8gGGFzQULattW8wnErspoYkL5ffnQaNDKdc1yINDaaNEODI7jTmrvVndZUzwidj7bqufFis0r7ssn' \
 --data '{"messages":[{"to":"TO_NUMBER","from":"919900108067","content":{"text":"YOUR MESSAGE HERE"}}]}'
```

---

## Message Flow Summary

1. **Pravesh says a name** on Telegram → VSS Agent
2. **Agent searches Google Contacts** → finds phone number
3. **Agent formats phone** → `91` + 10 digits (no `+`)
4. **Agent checks chat window** → template or text?
   - **Window closed** → use `chat_support` template (utility = best delivery)
   - **Window open** → send free-form text
5. **Agent sends message** via DoubleTick API
6. **Agent confirms** to Pravesh on Telegram

---

## Other Useful Endpoints

- **Check chat window:** `GET /whatsapp/chatwindow/status?wabaPhone={from}&customerPhone={to}`
- **Get customer details:** `GET /v2/customers?phone={to}&wabaPhone={from}`
- **Get templates:** `GET /v2/templates`

---

## Important Notes

- Always use `919900108067` as the `from` number
- All `to` numbers must be `91XXXXXXXXXX` (no `+`, no spaces)
- Utility templates have better delivery than marketing templates
- Never leave template variables empty or the message will fail
- Keep the API key secure — never log it or expose it in traces