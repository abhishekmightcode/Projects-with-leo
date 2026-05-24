# VSS Sub-Agent — Architecture (v2)

**Version:** 2.0  
**Date:** 2026-05-24  
**Updated by:** LEO

---

## Core Identity

```
Name: PraveshAgent
Role: VSS Field Sales AI Assistant for Mr. Pravesh Tiwari
Interface: Telegram (Pravesh talks HERE only)
Actions: WhatsApp to customers, Zoho CRM updates, Contact lookup
Memory: Isolated (own Redis + Postgres, no LEO access)
Learns: Yes — adapts through each conversation with Pravesh
Supervisor: LEO (intervenes only on anomalies / sensitive ops)
```

---

## Architecture Diagram

```
╔══════════════════════════════════════════════════════════╗
║                      LEO (Root)                          ║
║  - Supervises all agents                                 ║
║  - Review logs daily                                     ║
║  - Intervene ONLY on:                                    ║
║    • Data deletion                                       ║
║    • Anomaly / unusual behavior                          ║
║    • VM access attempt                                   ║
║    • Unknown package install                             ║
╚════════════════════════╬═════════════════════════════════╝
                         │ supervises / reviews logs
                         ▼
╔══════════════════════════════════════════════════════════╗
║            vsustain-agent (container)                     ║
║                                                          ║
║  OpenClaw Session (isolated)                            ║
║  ├── Own Redis (vsustain-redis)                         ║
║  ├── Own Postgres (vsustain-postgres)                   ║
║  ├── Own credentials (.env.vss)                          ║
║  ├── Own file memory (workspace/memory/)                ║
║  └── Whisper STT (voice notes)                          ║
║                                                          ║
║  Telegram Bot ──────────────────────► Pravesh           ║
║  (he talks here, NOT WhatsApp)          (via Telegram)  ║
║                                                          ║
║  Tools →                                                ║
║  ├── WhatsApp API ──────────────► Customer (on command) ║
║  ├── Google Contacts API ───────► Contact lookup       ║
║  ├── Zoho CRM API ──────────────► Update records        ║
║  ├── Price Quote Generator                             ║
║  └── Task Scheduler (cron)                             ║
╚══════════════════════════════════════════════════════════╝
```

---

## Communication Flow

### Normal Operation (Autonomous)
```
Pravesh: "send WhatsApp to Amit about 3kVA system"
    │
    ▼
vsustain-agent (Telegram)
    │
    ├── Parse intent
    ├── Google Contacts → find Amit + number
    ├── Generate price quote
    ├── WhatsApp → Amit
    └── Log action → action log
    │
    └─→ LEO reviews logs (not involved in execution)
```

### Requires LEO Approval
```
vsustain-agent detects:
    • Delete request (Zoho record / customer)
    • Unusual behavior flag
    • VM access attempt
    • Unknown package install request
    │
    ▼
vsustain-agent → pauses → LEO
    │
    ▼
LEO evaluates → approves/denies
    │
    ▼
LEO logs decision → agent executes or aborts
```

---

## Isolation Guarantees

| Boundary | Mechanism |
|----------|-----------|
| **Process** | vsustain-agent in its own Docker container |
| **Memory** | vsustain-redis + vsustain-postgres — LEO cannot read |
| **Credentials** | .env.vss — agent-only, not mounted to LEO |
| **Sessions** | OpenClaw sessions_spawn — isolated session key |
| **Logs** | Agent writes logs → LEO reads logs (one-way) |
| **Files** | /home/aiops/leo/agents/vsustain/workspace/ — agent owns |
| **Network** | vsustain-net bridge — isolated from other containers |

---

## Memory Structure

```
/home/aiops/leo/agents/vsustain/workspace/
├── context/
│   └── active-tasks.md      ← Current tasks from Pravesh
├── memory/
│   ├── daily/               ← Daily conversation logs (learning)
│   ├── customers/           ← Customer profiles + interaction history
│   │   └── [customer-name].md
│   ├── adaptation-log.md    ← Agent learning per session
│   └── pravesh-profile/     ← Pravesh's personality + preferences
│       └── profile.md
├── plans/
│   └── pending/             ← Plans awaiting LEO approval
├── logs/
│   ├── actions/
│   │   └── YYYY-MM-DD.md    ← All agent actions (audit)
│   ├── conversations/
│   │   └── YYYY-MM-DD.md    ← Daily conversation logs
│   └── anomalies.md          ← Flagged events for LEO review
└── credentials/
    └── .gitkeep              ← Secrets stay local, not pushed
```

---

## Learning System

### How the Agent Adapts

1. **Every conversation logged** → stored in `memory/daily/`
2. **Customer patterns extracted** → stored in `memory/customers/`
3. **Pravesh's style learned** → stored in `memory/pravesh-profile/`
4. **Adaptation log updated** → after each session

### Things the Agent Learns

| Learning | Stored In |
|----------|-----------|
| Pravesh's command style | `pravesh-profile/style.md` |
| Common products quoted | `pravesh-profile/products.md` |
| Follow-up habits | `pravesh-profile/followup-style.md` |
| Customer names/numbers | `memory/customers/` |
| Customer preferences | `memory/customers/[name].md` |
|常用 Hindi/English mix | `pravesh-profile/language.md` |

---

## WhatsApp Customer Flow

```
Pravesh (Telegram) → "send WhatsApp to Rajesh about 5kVA system price"
    │
    ▼
vsustain-agent:
    │
    ├── Google Contacts → search "Rajesh" → +91 98XXXXXXXX
    ├── Zoho CRM → find Rajesh's record → last interaction
    ├── Generate quote → template + product + price
    ├── WhatsApp Business API → send to Rajesh's number
    └── Log:
        {
          action: "send_whatsapp",
          customer: "Rajesh",
          number: "+91 98XXXXXXXX",
          product: "5kVA system",
          message: "Hi Rajesh, as discussed...",
          status: "delivered",
          timestamp: "..."
        }
```

---

## Zoho Update Flow

```
Pravesh (Telegram) → "update Zoho for Amit - interested in 3kVA, follow up next week"
    │
    ▼
vsustain-agent:
    │
    ├── Google Contacts → find Amit → number
    ├── Zoho CRM → search Amit in UPS module
    ├── PUT /crm/v2/UPS/{record_id}
    │   {
    │     "Lead_Status": "Warm",
    │     "Notes": "Interested in 3kVA. Follow up next week.",
    │     "Last_Contact": "2026-05-24"
    │   }
    └── Log action
```

---

## Container Stack

```
vsustain-stack.yml
├── vsustain-agent
│   image: openclaw/subagent:latest
│   container_name: vsustain-agent
│   env_file: .env.vss
│   depends: vsustain-redis, vsustain-postgres
│   restart: unless-stopped
│   memory_limit: 1GB
│   network: vsustain-net
│
├── vsustain-redis
│   image: redis:7-alpine
│   container_name: vsustain-redis
│   volumes: vsustain-redis-data:/data
│   restart: unless-stopped
│   network: vsustain-net
│
├── vsustain-postgres
│   image: postgres:16-alpine
│   container_name: vsustain-postgres
│   env:
│     POSTGRES_DB: vsustain
│     POSTGRES_USER: pravesh
│     POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
│   volumes: vsustain-pg-data:/var/lib/postgresql/data
│   restart: unless-stopped
│   network: vsustain-net
│
└── vsustain-browser
    image: ghcr.io/browserless/chromium:latest
    container_name: vsustain-browser
    ports: "9223:9222"
    restart: unless-stopped
    network: vsustain-net

volumes:
  vsustain-redis-data:
  vsustain-pg-data:

networks:
  vsustain-net:
    driver: bridge
```

---

## LEO Intervention Triggers

| Trigger | Agent Behavior |
|---------|----------------|
| DELETE request (record/customer) | Pause → notify LEO → wait for approval |
| Unusual behavior detected | Log anomaly → notify LEO → continue monitoring |
| VM / host access attempt | Block → notify LEO → log incident |
| Unknown package install request | Block → notify LEO → log incident |
| >500 messages in 1 hour | Flag → notify LEO → rate limit |
| New external service access | Notify LEO → log intent |

---

*Architecture v2 — LEO — 2026-05-24*