# VSS Sub-Agent — Master Plan (v2)

**Project:** Pravesh AI Agent for VSS  
**Version:** 2.0  
**Date:** 2026-05-24  
**Updated by:** LEO  
**Owner:** Abhishek Sharma (@abhishekmightcode)  
**Beneficiary:** Pravesh Kumar Tiwari (Mr. Pravesh)

---

## What Changed in v2

- Pravesh talks to the agent **via Telegram only** (not WhatsApp for himself)
- Agent sends WhatsApp messages **to Pravesh's customers** on Pravesh's verbal command
- Agent searches **Google Contacts** to find customer name + number
- Agent updates **Zoho CRM** via API calls on verbal command
- **Immediate priority:** Agent live on Telegram now → Abhishek tests → then hands to Pravesh
- Agent **learns and adapts** through each conversation with Pravesh
- LEO approval only for: data deletion, anomaly, unusual behavior, VM access, unknown package install

---

## How Pravesh Will Use the Agent

```
Pravesh (verbal/telegram) → "send WhatsApp to Rajesh about 5kVA system price"
         │
         ▼
   PraveshAgent (Telegram bot)
         │
         ├── Searches Google Contacts → finds Rajesh's number
         ├── Generates price quote
         └── Sends WhatsApp to Rajesh
              │
         (agent logs action)

Pravesh (verbal/telegram) → "update Zoho for Amit - discussed 3kVA, interested"
         │
         ▼
   PraveshAgent (Telegram bot)
         │
         ├── Searches Google Contacts → finds Amit
         ├── Finds Amit in Zoho CRM
         └── PUT call to Zoho: notes + status update
```

---

## Architecture (Updated)

```
                    ┌─────────────────────────────┐
                    │     Pravesh (Telegram)      │
                    │  ← He talks HERE only        │
                    └──────────────┬──────────────┘
                                   │ Telegram DM
                                   ▼
┌──────────────────────────────────────────────────┐
│           vsustain-agent (container)              │
│                                                   │
│  Identity: "Pravesh's AI Assistant"              │
│  Personality: Trained by Abhishek + Pravesh       │
│  Language: Hindi/English (Pravesh's mix)         │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │  Sessions (OpenClaw)                       │  │
│  │  - Own isolated session                    │  │
│  │  - Own memory (Redis + Postgres)          │  │
│  │  - Own credentials (VSS only)              │  │
│  │  - learns from every conversation         │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  Tools:                                           │
│  ├── WhatsApp (send to customers)                │
│  ├── Google Contacts (search)                     │
│  ├── Zoho CRM (read/write VSS)                   │
│  ├── Price quote generator                        │
│  └── Task scheduler                              │
└───────────────────────┬──────────────────────────┘
                        │ supervised by
                        ▼
┌──────────────────────────────────────────────────┐
│            LEO (Root Orchestrator)               │
│                                                   │
│  Supervises:                                      │
│  - Logs review (daily)                           │
│  - Anomaly detection                             │
│  - Approval for sensitive ops                    │
│                                                   │
│  LEO intervene ONLY when:                        │
│  - Data deletion requested                       │
│  - Anomaly/unusual behavior                     │
│  - VM access attempt                             │
│  - Unknown package install                       │
└──────────────────────────────────────────────────┘
                        ▲
                        │ reports to
                        │
                  Abhishek (monitors)
```

---

## Memory & Learning

### How the Agent Learns

Each conversation with Pravesh is stored in:
```
/vsustain-agent/workspace/memory/
├── daily/                    ← Daily conversation logs
├── customers/                ← Customer profiles (known preferences)
├── pravesh-profile/          ← Pravesh's personality, style, preferences
└── adaptation-log.md         ← What agent learned this session
```

### Adaptation Tracked
- **Communication style** — how Pravesh gives commands
- **Product preferences** — what products he quotes often
- **Follow-up patterns** — when he follows up, how he follows up
- **Customer names** — who's who in his network
- **常用 phrases** — his common expressions

**Privacy:** Pravesh's customer data stays in agent memory only. LEO doesn't read it unless escalated.

---

## Isolation Layers

| What PraveshAgent CAN | What PraveshAgent CANNOT |
|------------------------|--------------------------|
| Access VSS CRM | Access LEO's memory |
| Send WhatsApp to customers | Access other agent memory |
| Search Google Contacts | Delete data without LEO approval |
| Update Zoho records | Access VM / install packages |
| Learn from Pravesh's conversations | Reach other cohort data |
| Log all actions for review | Bypass audit trail |

---

## Immediate Priority: Agent Live on Telegram

### Phase 0 — Telegram Bot (THIS WEEK)

**Goal:** Abhishek tests the agent on Telegram now. Pravesh gets it later.

```
Step 1: Create Telegram bot for PraveshAgent
        → Abhishek creates bot via @BotFather
        → shares token with LEO

Step 2: LEO deploys vsustain-agent container
        → isolated Docker container
        → own Redis + Postgres
        → OpenClaw manages session

Step 3: Connect agent to Pravesh's Telegram bot
        → routes messages to vsustain-agent session
        → agent responds via Telegram

Step 4: Abhishek tests
        → trains agent on Pravesh's personality
        → shares info about Pravesh (name, style, business)
        → agent learns through conversation

Step 5: Hand to Pravesh
        → Pravesh talks to it
        → Abhishek monitors logs
        → refine based on real usage
```

### What's Already Installed (reuse for this agent)

| Component | Already On VM | Can Reuse |
|-----------|--------------|-----------|
| Whisper STT | ✅ | Yes |
| Redis | ✅ (leo-redis) | Need new vsustain-redis |
| Postgres | ✅ (leo-postgres) | Need new vsustain-postgres |
| Docker | ✅ | Yes |
| OpenClaw | ✅ | Yes (sessions_spawn) |

---

## LEO Supervision Rules

| Action | Requires LEO Approval |
|--------|----------------------|
| Delete customer record | ✅ YES |
| Delete Zoho entry | ✅ YES |
| Unusual pattern (500 msgs/day) | ✅ YES |
| Attempt to access VM | ✅ YES |
| Install unknown package | ✅ YES |
| Send WhatsApp to customer | ❌ NO (autonomous) |
| Update CRM note | ❌ NO (autonomous) |
| Search contact | ❌ NO (autonomous) |
| Generate price quote | ❌ NO (autonomous) |
| Remember a task | ❌ NO (autonomous) |

---

## Audit Log

All agent actions logged to:
```
/vsustain-agent/workspace/logs/
├── actions/
│   ├── YYYY-MM-DD.md    ← Daily action log
│   └── anomalies.md     ← Flagged events
├── conversations/
│   └── YYYY-MM-DD.md    ← Daily conversation logs
└── reviews/
    └── LEO-review.md     ← LEO's periodic review notes
```

Log format per action:
```markdown
## [HH:MM] Action: send_whatsapp
- Trigger: "send to Rajesh about 5kVA" (verbal)
- Customer: Rajesh (from Google Contacts)
- Number: +91 98XXXXXXXX
- Message: "Hi Rajesh, as discussed..."
- WhatsApp status: delivered
- Reviewed: no (routine)
```

---

## Why 2GB Extra RAM?

| Use | RAM |
|-----|-----|
| vsustain-agent (OpenClaw session) | 512 MB |
| vsustain-redis (its own memory) | 256 MB |
| vsustain-postgres (customer data) | 512 MB |
| vsustain-browser (WhatsApp web) | 256 MB |
| Whisper STT (when transcribing) | 400 MB |
| **Total needed** | **~2 GB** |
| **Currently used** | ~2.1 GB |
| **Headroom** | ~0 MB ← NEED 2GB MORE |

**Without extra RAM:** Agent crashes when Whisper runs during a voice note + Postgres is active simultaneously.

---

## What's Needed to Start

| Item | Who Provides | Status |
|------|-------------|--------|
| Telegram Bot Token (for PraveshAgent) | Abhishek via @BotFather | ⏳ Needed |
| Zoho API token (VSS) | Abhishek | ⏳ Needed |
| Google Contacts API credentials | Abhishek | ⏳ Needed |
| WhatsApp Business API / n8n | Abhishek | ⏳ Needed |
| Pravesh profile info | Abhishek → train agent | ⏳ Needed |

---

## Timeline (Updated)

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 0** | This week | Telegram bot live → Abhishek tests |
| Phase 1 | Week 1-2 | Zoho + Contacts integration |
| Phase 2 | Week 3-4 | WhatsApp customer send |
| Phase 3 | Week 5+ | Full autonomy + learning |

---

## Docs Location

```
Projects-with-leo/
└── COHORTS/VSS/AGENT/
    ├── PLANS/MASTER-PLAN-v2.md  ← You are here
    ├── ARCHITECTURE/AGENT-ARCHITECTURE.md
    ├── DEPLOYMENT/DEPLOYMENT-PLAN.md
    └── LOGGING/AUDIT-LOG-FORMAT.md
```

---

*v2 — LEO — 2026-05-24*  
*Update: Pravesh Telegram-first, learning agent, LEO approval only on sensitive ops*