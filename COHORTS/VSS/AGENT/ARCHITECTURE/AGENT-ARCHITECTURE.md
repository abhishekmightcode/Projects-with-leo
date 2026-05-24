# VSS Sub-Agent — Architecture

**Project:** VSS Pravesh AI Agent (vsustain-agent)  
**Type:** Containerized Worker Sub-Agent  
**Parent:** LEO (Root Orchestrator)  
**Cohort:** VSS  
**Owner:** Abhishek Sharma (@abhishekmightcode)

---

## Why a Separate Sub-Agent?

- **Isolation:** Pravesh's agent should never access LEO's memory, credentials, or other project data
- **Focus:** VSS agent knows ONLY about Pravesh's tasks, customers, and CRM
- **Security:** If vsustain-agent is compromised, it can't reach LEO or other cohorts
- **Scaling:** Agent can be upgraded/restarted independently without affecting LEO

---

## Agent Identity

```
Name: Pravesh
Role: VSS Field Sales AI Assistant
Owner: Pravesh Kumar Tiwari (Mr. Pravesh)
Parent: LEO (infrastructure orchestrator)
Access: VSS CRM, WhatsApp, Google Contacts, scheduled tasks ONLY
Memory: Isolated — own Redis + file memory, no access to LEO's memory
```

---

## Architecture

```
LEO (Root Orchestrator)
    │
    │  supervise / coordinate / plan
    │  ← receives updates from Pravesh
    │  ← reviews agent's work
    │
    ▼
┌──────────────────────────────────────────┐
│         vsustain-agent (container)       │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  pravesh-sub-agent (session)       │  │
│  │  - Isolated memory                 │  │
│  │  - Own Redis (vsustain-redis)      │  │
│  │  - Own workspace                   │  │
│  │  - Speaks Hindi/English            │  │
│  │  - Voice command aware             │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Tools:                                  │
│  ├── WhatsApp API (via n8n/wa-js)        │
│  ├── Zoho CRM (read/write VSS module)    │
│  ├── Google Contacts (read)              │
│  ├── Google Messages (read/reply)        │
│  ├── Price quotation generator           │
│  ├── Task scheduler (cron)               │
│  └── Web search (market research)        │
└──────────────────────────────────────────┘
    │
    ├── vsustain-redis (container)         │ ← Isolated Redis
    ├── vsustain-postgres (container)       │ ← Isolated Postgres
    └── vsustain-browser (chromium)         │ ← Browser automation
```

---

## Isolation Layers

| Layer | What Pravesh Agent CAN Access | What Pravesh Agent CANNOT Access |
|-------|-------------------------------|----------------------------------|
| **Memory** | Own Redis, own file memory | LEO's memory, other cohort memory |
| **Credentials** | VSS-specific tokens only | LEO's GitHub token, other project creds |
| **Sessions** | Only Pravesh's session | LEO's main session, other agents |
| **Files** | /home/aiops/leo/agents/vsustain/ | /home/aiops/leo/ (LEO's root) |
| **Containers** | vsustain-agent, vsustain-redis | LEO's container, other agent containers |

---

## Memory Architecture

```
vsustain-agent workspace:
/home/aiops/leo/agents/vsustain/
├── context/
│   └── active-tasks.md        ← What Pravesh asked for right now
├── memory/
│   ├── daily/                 ← Daily logs
│   └── customers/             ← Customer profiles + interaction history
├── credentials/
│   └── .env.vss               ← VSS only: WhatsApp token, Zoho token
└── plans/
    └── pending-plans.md       ← Plans awaiting LEO approval
```

**No cross-contamination:** If LEO's session resets, LEO's memory is intact. Pravesh's agent doesn't touch it.

---

## Capabilities

### Core Tasks
1. **WhatsApp Integration**
   - Send price quotations (auto-generated PDF/Text)
   - Send follow-up messages (scheduled)
   - Reply to customer queries (with LEO escalation)
   - Broadcast messages to customer list

2. **CRM Operations (Zoho)**
   - Read dealer/customer records
   - Update dealer info
   - Create Dealer Meets entries
   - Log calls and visits
   - Fetch recent interactions

3. **Task Management**
   - Remember tasks for Pravesh
   - Schedule follow-ups
   - Set reminders
   - Create automations (approved by LEO)

4. **Research & Help**
   - Market research on request
   - Product price lookup
   - Concept teaching (solar, sales)
   - competitor analysis

5. **Communication**
   - Voice note understanding (via Whisper STT)
   - Hindi/Hindi-English mixed responses
   - Simple clear instructions

---

## Integration Points

| Service | How Connected | Purpose |
|---------|---------------|---------|
| **Zoho CRM** | Direct API (`crm.zoho.in`) | VSS module read/write |
| **WhatsApp** | n8n webhook or wa-js | Message delivery |
| **Google Contacts** | Google API | Customer contact sync |
| **Google Messages** | Google Messages API | SMS read/reply |
| **LEO** | Redis pub/sub + file | Status updates, escalation |
| **n8n** | Webhook triggers | Automation workflows |

---

## Supervised Autonomy

Pravesh agent operates under LEO supervision:

```
Pravesh → speaks to → Pravesh Agent → acts
                                       │
                          If complex/unusual → LEO approval needed
                                       │
                                  LEO reviews → approves/denies
                                       │
                              LEO updates project docs
```

**L3 Autonomous Actions** (Pravesh agent can do alone):
- Send follow-up message (if context exists)
- Read CRM for customer info
- Generate price quotation (template-based)
- Remember a task
- Search web for info

**L2 Supervised Actions** (Pravesh agent asks LEO first):
- Send new automation plan
- Create new workflow
- Access new data source
- Modify CRM schema

**L1 Escalation** (Pravesh agent → LEO → Abhishek):
- Security concerns
- Unusual behavior
- Major strategic decisions

---

## Container Stack

```
vsustain-stack.yml (docker-compose)
├── vsustain-agent
│   image: openclaw-agent:vss
│   context: /home/aiops/leo/agents/vsustain/
│   env_file: .env.vss
│   depends: vsustain-redis, vsustain-postgres
│   restart: unless-stopped
│   memory_limit: 1GB
│
├── vsustain-redis
│   image: redis:7-alpine
│   volumes: vsustain-redis-data:/data
│   restart: unless-stopped
│
├── vsustain-postgres
│   image: postgres:16-alpine
│   volumes: vsustain-pg-data:/var/lib/postgresql/data
│   restart: unless-stopped
│   env:
│     POSTGRES_DB: vsustain
│     POSTGRES_USER: pravesh
│
└── vsustain-browser
    image: ghcr.io/browserless/chromium:latest
    ports: "9223:9222"
    restart: unless-stopped
```

---

## File Structure

```
/home/aiops/leo/agents/vsustain/
├── docker-compose.yml
├── Dockerfile.agent
├── .env.vss                      ← VSS CREDENTIALS ONLY (not pushed to git)
├── agent-config.yml
├── workspace/
│   ├── context/
│   │   └── active-tasks.md
│   ├── memory/
│   │   ├── daily/
│   │   └── customers/
│   ├── plans/
│   │   └── pending/
│   └── credentials/
│       └── .gitkeep             ← actual secrets stay local
├── tools/
│   ├── whatsapp-sender.py
│   ├── zoho-crm-client.py
│   ├── price-quotation-gen.py
│   └── task-scheduler.py
└── logs/
```

---

*Architecture v1.0 — 2026-05-24*  
*Designed by LEO for VSS Pravesh Agent*