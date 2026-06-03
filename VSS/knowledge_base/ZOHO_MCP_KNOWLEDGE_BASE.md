# ZOHO MCP — Knowledge Base
**For:** VSustainAI ☀️  
**Created by:** LEO 🦁  
**Date:** 2026-05-28  
**Status:** ACTIVE — Zoho MCP integration in progress

---

## What is Zoho MCP?

**Zoho MCP (Model Context Protocol)** is a standardized protocol bridge that connects AI agents (like VSustainAI) to Zoho's business applications — CRM, Books, Desk, Mail, Calendar, and 500+ third-party apps.

> **Official site:** https://www.zoho.com/mcp/  
> **Signup:** https://www.zoho.com/mcp/signup.html

---

## Why It Matters for VSustainAI

VSustainAI manages solar sales/CRM operations. Zoho MCP enables:

- **Natural language CRM operations** — *"Create a lead for ABC Solar"*, *"Update deal stage to Won"*
- **Cross-app automation** — Zoho CRM + Zoho Books + Gmail working together
- **Autonomous agents** — VSustainAI can monitor and act without being prompted
- **500+ integrations** — Notion, GitHub, Stripe, Twilio, Freshsales, and more

---

## Supported Zoho Apps (confirmed)

| App | What you can do |
|-----|----------------|
| **Zoho CRM** | Create/update/delete leads, contacts, deals, accounts; log activities; send emails |
| **Zoho Desk** | Manage support tickets, escalate, auto-reply |
| **Zoho Books** | Generate invoices, track expenses, financial reports |
| **Zoho Mail** | Send/receive emails, manage folders |
| **Zoho Calendar** | Schedule meetings, set reminders |
| **Zoho People** | HR records (for team ops) |
| **Zoho Expense** | Track and submit expenses |
| **Zoho Creator** | Custom app data operations |

---

## Sample Prompts (what AI agents can do)

### Sales / CRM
```
"Mark the Zylker deal as won and schedule a call with John for onboarding"
"Create a new lead for ABC Solar with email solar@abcsolar.com"
"Show all open leads from Bangalore region"
"Update deal value to ₹2,50,000 for SunPower installation"
```

### Marketing
```
"Schedule a campaign called 'Summer Sale' for next Tuesday at 11 AM targeting leads from Bangalore"
"Generate a report of all leads added this month"
```

### Support
```
"Search Zoho Desk for open tickets. Mark them in progress and reply that we're working on it"
"Escalate all tickets older than 48 hours"
```

### Finance
```
"Generate an invoice for Naveen Kumar from ABC Corp for ₹1200 on consulting services"
"Track payment status for invoice #VSS-2026-001"
```

---

## Architecture — How It Works

```
VSustainAI (you)
    ↓ natural language
Zoho MCP Server (hosted by Zoho)
    ↓ REST API
Zoho Apps (CRM, Books, Desk, etc.)
```

**Two modes:**
1. **Prompt-based** — You send a prompt, MCP executes actions
2. **Autonomous** — VSustainAI monitors and acts on its own (e.g., overnight ticket escalation)

---

## Authentication

Zoho MCP uses **OAuth-based authorization**.

To connect, you need:
- A Zoho account
- Zoho MCP workspace setup at zoho.com/mcp/signup.html
- An **Access Token** (OAuth token)
- A **Data Center** URL (depends on your Zoho region: .com, .in, .eu, etc.)

**Token format:** `Zoho-oauthtoken` header or Bearer token in HTTP headers

---

## Configuration in OpenClaw

Once credentials are obtained, add to OpenClaw config via `gateway` tool:

```json
{
  "mcp": {
    "servers": {
      "zoho-crm": {
        "url": "https://mcp.zoho.com",
        "transport": "streamable-http",
        "headers": {
          "Authorization": "Bearer YOUR_TOKEN"
        }
      }
    }
  }
}
```

Or using CLI:
```bash
openclaw mcp set zoho-crm '{"url":"https://mcp.zoho.com","transport":"streamable-http"}'
```

---

## MCP Tools Available (Zoho CRM example)

Once connected, VSustainAI can call these tool-style actions:

| Tool | What it does |
|------|-------------|
| `crm_create_lead` | Create new lead with name, email, phone, company |
| `crm_update_deal` | Update deal stage, value, close date |
| `crm_search_contacts` | Find contacts by name, email, phone |
| `crm_log_activity` | Log a call, meeting, or task |
| `desk_create_ticket` | Create support ticket |
| `desk_reply_ticket` | Add reply to open ticket |
| `books_create_invoice` | Generate invoice |
| `books_send_invoice` | Email invoice to customer |

---

## Integration with VSustainAI Workflows

**Your current WhatsApp workflow:**
```
Inbound WhatsApp → process_message() → DoubleTick → Zoho CRM (manual step)
```

**With Zoho MCP, the CRM step becomes:**
```
Inbound WhatsApp → process_message() → DoubleTick → Zoho MCP → Zoho CRM (automatic!)
```

**Example flow:**
1. Customer replies on WhatsApp interested in solar panels
2. `process_message()` triggers → `zoho_crm_create_lead()` with customer details
3. VSustainAI logs the interaction in CRM without human help
4. Deal is created, follow-up scheduled automatically

---

## Real-World VSustainAI Use Cases

### Lead Capture
- WhatsApp inquiry → auto-create Zoho CRM Lead
- Extract: name, phone, email, location, requirement
- Assign to sales rep automatically

### Follow-up Automation
- Deal stage changes → trigger WhatsApp follow-up via DoubleTick
- Overdue follow-ups → auto-escalate to manager

### Invoice Generation
- Deal marked "Won" → create Zoho Books invoice
- Send invoice via WhatsApp or Email automatically

### Support Ticket Management
- Customer complains on WhatsApp → create Zoho Desk ticket
- Ticket auto-assigned to available rep
- Resolution status sent back to customer on WhatsApp

---

## Setup Status

| Step | Status |
|------|--------|
| Sign up at zoho.com/mcp/signup.html | ⏳ PENDING — needs Abhishek |
| Get OAuth token | ⏳ PENDING |
| Configure in OpenClaw | ⏳ PENDING |
| Test CRM operations | 🔴 NOT STARTED |
| Integrate with WhatsApp workflow | 🔴 NOT STARTED |

---

## Resources

- **Official site:** https://www.zoho.com/mcp/
- **Signup:** https://www.zoho.com/mcp/signup.html
- **OpenClaw MCP docs:** `/usr/lib/node_modules/openclaw/docs/cli/mcp.md`
- **Testimonial (OpenClaw + Zoho):** Tushar Khattar, Once Upon Me — uses Zoho Books + Claude + OpenClaw

---

## Key Quotes from Zoho's Marketing

> *"Turn natural language into real business outcomes"*

> *"Work won't happen in tabs anymore. It'll happen through agents."*

> *"Zoho MCP, along with Zoho Books, has transformed the way we handle accounting workflows. By integrating with OpenClaw, we're able to manage bills, invoices, and routine bookkeeping through simple AI-driven instructions."* — Tushar Khattar, Co-Founder Once Upon Me

---

*Last updated: 2026-05-28 by LEO 🦁*
