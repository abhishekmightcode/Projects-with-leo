# VSS Sub-Agent — Master Plan

**Project:** Pravesh AI Agent for VSS  
**Version:** 1.0  
**Date:** 2026-05-24  
**Created by:** LEO (Root Infrastructure Orchestrator)  
**Owner:** Abhishek Sharma (@abhishekmightcode)  
**Cohort:** VSS (V Sustain Solar Solutions)  
**Beneficiary:** Pravesh Kumar Tiwari (Mr. Pravesh)

---

## What Are We Building?

An AI agent that lives in a container, serves Mr. Pravesh (VSS owner), handles his day-to-day sales tasks via voice commands, and reports to LEO for supervision.

**Pravesh talks to it → It does the work → LEO supervises → Abhishek monitors**

---

## Problem Statement

Pravesh is the owner of VSS. He does field sales and manages customers. Currently:
- He forgets follow-ups → customers go cold
- He sends price quotes manually → slows him down
- He can't keep track of all customer interactions → CRM is underutilized
- He relies on WhatsApp messages to track everything → chaotic

**What he wants:** An AI assistant he can talk to, that handles CRM, sends WhatsApp messages, schedules tasks, and keeps everything organized.

---

## Solution Overview

```
Pravesh (voice/text WhatsApp)
         │
         ▼
┌─────────────────────────┐
│   PraveshAgent (container)
│   ├── Speaks Hindi/English
│   ├── Voice command understanding
│   ├── WhatsApp integration
│   ├── Zoho CRM read/write
│   ├── Task scheduling
│   └── Isolated memory (own Redis/Postgres)
└────────────┬────────────┘
             │ supervised by
             ▼
┌─────────────────────────┐
│   LEO (root orchestrator)
│   ├── Reviews agent's work
│   ├── Approves new automations
│   ├── Updates project docs
│   └── Escalation point
└────────────┬────────────┘
             │ reports to
             ▼
Abhishek (monitors everything)
```

---

## Features (Priority Order)

### P0 — Must Have (Month 1)

1. **Price Quotation on WhatsApp**
   - "Send price quote to customer X for 3kVA system"
   - Agent generates formatted quote → sends via WhatsApp

2. **Follow-up Message Scheduler**
   - "Remind me to follow up with customer Y tomorrow"
   - Agent schedules message → sends automatically

3. **CRM Query**
   - "Show me today's follow-ups"
   - "Add notes to dealer Z"
   - "Log a call with customer W"

4. **Task Memory**
   - "Remember that Mr. R wants a 5kW system"
   - Agent stores in customer memory → recalls when relevant

### P1 — Should Have (Month 2)

5. **Google Contacts Integration**
   - Pull customer phone numbers from contacts
   - Match with CRM records

6. **Market Research**
   - "What is the price of 5kW solar panel from Luminous?"
   - "Who is Luminous's competitor in Bangalore?"

7. **Call Logging**
   - "Log a call with customer X - discussed 3kVA system, interested"
   - Agent writes to Zoho CRM Dealer Meets

### P2 — Nice to Have (Month 3)

8. **Google Messages Integration**
   - Read incoming SMS
   - Auto-reply for simple queries

9. **Automation Creator**
   - "Create a workflow: every new VSS lead → send welcome message"
   - Agent builds in n8n → LEO approves → deploys

10. **Concept Teaching**
    - "Explain solar panel efficiency"
    - "Teach me about net metering"
    - Agent uses web search + knowledge base

---

## Multi-Project Context (How LEO Tracks)

Abhishek has 4 active projects/cohorts:
- **VSS** ← This agent
- **PanaceaX** ← Zoho CRM research
- **Solar-Bangalore** ← Paused
- **Agency-Clients** ← Client work

When Abhishek says "work on VSS", LEO routes to vsustain-agent.
When Abhishek says "work on PanaceaX", LEO handles directly.

Each agent has **isolated memory** — Pravesh's agent can't see PanaceaX docs.

---

## Memory Isolation (Critical)

| Agent | Memory | Can Access |
|-------|--------|-----------|
| **LEO** (root) | Main Redis + file | Everything |
| **vsustain-agent** | Own Redis + Postgres | VSS only, NOT LEO's memory |
| **future agents** | Own isolated stores | Own cohort only |

This is by design — security and privacy.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Runtime | OpenClaw sub-agent session |
| Container | Docker (vsustain-agent) |
| Memory | Redis (short-term) + Postgres (long-term) |
| CRM | Zoho CRM (`crm.zoho.in`) |
| Messaging | WhatsApp Business API / n8n |
| Contacts | Google Contacts API |
| Voice | Whisper STT (already installed) |
| Browser | Chromium (for WhatsApp Web automation) |

---

## Timeline

| Week | Deliverable |
|------|-------------|
| Week 1 | Infrastructure setup (Docker, Redis, Postgres, Agent config) |
| Week 2 | WhatsApp + Zoho integration |
| Week 3 | Price quote + follow-up scheduler |
| Week 4 | Voice command pipeline + testing |
| Week 5 | Pilot with Pravesh |
| Week 6+ | Refinement + P1 features |

---

## What LEO Needs from Abhishek to Proceed

1. **WhatsApp Business API access** — or confirm n8n WhatsApp approach
2. **Zoho API tokens** — create if not already done (DC: `.in`)
3. **Pravesh's phone number** — test user
4. **VSS product catalog** — for price quotation templates
5. **Approval** — to start Phase 1 (infrastructure)

---

## Documentation Repo

All docs live at:
**https://github.com/abhishekmightcode/Projects-with-leo**

```
COHORTS/VSS/AGENT/
├── ARCHITECTURE/
│   └── AGENT-ARCHITECTURE.md
├── DEPLOYMENT/
│   └── DEPLOYMENT-PLAN.md
└── PLANS/
    └── MASTER-PLAN.md  ← This file
```

---

*Plan created by LEO — 2026-05-24*  
*For: VSS Pravesh AI Agent*  
*Supervised by: LEO*  
*Owned by: Abhishek Sharma*