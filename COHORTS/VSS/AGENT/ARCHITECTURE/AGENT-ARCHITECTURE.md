# VSS Sub-Agent — Architecture (v3)

**Version:** 3.0  
**Date:** 2026-05-25  
**Updated by:** LEO  

---

## Objective

Build VSustain as a completely isolated operational AI agent under the ROOTAI/LEO ecosystem.

**Why v3?** Previous architecture failed because:
- Telegram routing contamination occurred
- Multiple agents shared the same runtime
- Agent identity boundaries were weak
- Sessions and routing collided
- OpenClaw default agent state became polluted

This architecture prevents all of this completely.

---

## Final Target Architecture

```
BARE METAL HOST (AIforce)
│
├── ROOTAI / LEO
│   ├── Telegram: @Chotarajandonbot
│   ├── Orchestrator
│   ├── Governance
│   ├── Infrastructure control
│   ├── Observability
│   ├── Memory summaries
│   ├── Task delegation
│   └── Global audit authority
│
├── Docker Network
│
├── vss-agent-container
│   ├── OpenClaw Runtime
│   ├── VSustain Identity
│   ├── Telegram: @VSustainAIbot
│   ├── Independent sessions
│   ├── Independent memory
│   ├── Independent workspace
│   ├── Independent filesystem
│   ├── Independent logs
│   ├── Independent PostgreSQL schema
│   ├── Independent Redis namespace
│   └── Independent browser workers
│
└── Shared Infrastructure Layer
    ├── PostgreSQL
    ├── Redis
    ├── Grafana
    ├── Prometheus
    ├── Loki
    ├── Uptime Kuma
    └── Browserless Chromium
```

---

## Core Principle

**LEO must NEVER directly host business agents.**

| LEO Should | VSS Agent Should |
|------------|------------------|
| Orchestrate | Live inside isolated container |
| Monitor | Own its own memory |
| Audit | Own its own Telegram identity |
| Delegate | Own its own sessions |
| Govern | Own its own workflows |

**This prevents:** identity contamination, routing collisions, memory corruption, session bleed, orchestration conflicts.

---

## Telegram Architecture

| Bot | Purpose |
|-----|---------|
| **@Chotarajandonbot** | LEO — infrastructure, orchestration, operator interface |
| **@VSustainAIbot** | VSS agent — customer interactions, business workflows, sales operations |

---

## Critical Rule

**NO runtime should EVER host multiple business identities.**

One runtime = one identity. Always.

---

## Infrastructure Layers

### Layer 1 — ROOT Orchestrator (LEO)

**Host User:** `aiops@AIforce`

| Responsibility | Description |
|----------------|-------------|
| Infrastructure orchestration | Container lifecycle, networking |
| Governance | Policy enforcement, permissions |
| Memory summarization | Condensed memory for cross-agent coherence |
| Audit systems | Global action logging |
| Delegation | Task routing to business agents |
| Scheduling | Cron, heartbeats, delayed work |
| Monitoring | Health, metrics, alerting |
| Recovery | Restart failed agents |
| Global routing | Telegram routing coordination |

**LEO SHOULD NEVER:**
- Manage customer conversations
- Run business workflows directly
- Operate sales pipelines
- Own company memory

### Layer 2 — Business Agent Containers

Each business gets:
- One isolated runtime
- One isolated OpenClaw
- One isolated Telegram bot
- One isolated workspace
- One isolated memory scope
- One isolated filesystem

Future agents: `vss-agent`, `qenix-agent`, `panaceax-agent`, `research-agent`, `content-agent`

---

## VSustain Container Structure

**Container Name:** `vss-agent`

**Internal Paths:**
```
/workspace
/workspace/memory
/workspace/logs
/workspace/governance
/workspace/tasks
/workspace/audits
```

**Persistent Host Mount:** `/home/aiops/agents/vss/`

**Mapped Into Container:** `/workspace`

---

## Memory Architecture

VSS memory should **NOT** share direct sessions with LEO.

### VSS Owns (Business Data)
- Customer memory
- Sales memory
- Lead memory
- Project memory
- Business workflows
- Conversation history

### LEO Receives ONLY
- Summaries
- Operational audits
- Health reports
- Metrics
- Task outcomes
- Critical escalations

**This is Memory Federation — NOT shared consciousness.**

---

## PostgreSQL Architecture

**Database:** `leo_memory`  
**Schema:** `vss`

Shared database, isolated schema — prevents proliferation of DB instances.

```
leo_memory.vss.*
leo_memory.vss.customers
leo_memory.vss.interactions
leo_memory.vss.tasks
leo_memory.vss.audit
```

---

## Redis Architecture

**Recommended Namespace:** `vss:*`

```
vss:sessions
vss:memory
vss:tasks
vss:state
```

Isolated namespace within shared Redis instance.

---

## Container Template

```yaml
services:
  vss-agent:
    image: openclaw:latest
    container_name: vss-agent
    restart: unless-stopped
    environment:
      TELEGRAM_BOT_TOKEN: ${VSS_TELEGRAM_TOKEN}
      OPENCLAW_PROFILE: vss
    volumes:
      - /home/aiops/agents/vss:/workspace
    networks:
      - agent-network
    ports:
      - "18801:18789"
```

**Inside container, run:**
```bash
openclaw --profile vss gateway
```

This prevents: session contamination, config contamination, routing overlap.

---

## Governance Files

Every agent must have at `/workspace/governance/`:

| File | Purpose |
|------|---------|
| `identity.md` | Who the agent is, its role, boundaries |
| `rules.md` | Operational rules and constraints |
| `permissions.md` | What it can and cannot do |
| `escalations.md` | When and how to escalate to LEO |

### LEO Permissions

**Can:**
- Restart containers
- Deploy infrastructure
- Modify governance
- Audit systems

**Cannot:**
- Impersonate business agents
- Modify customer memory directly

### VSS Permissions

**Can:**
- Operate business workflows
- Manage CRM
- Talk to customers
- Run sales flows

**Cannot:**
- Modify infrastructure
- Restart host systems
- Access other agent memory

---

## Observability Design

Every agent exports to shared observability stack:

| Export | Tool |
|--------|------|
| Logs | Loki |
| Health | Prometheus + Uptime Kuma |
| Metrics | Prometheus |
| Heartbeat | Uptime Kuma |

### Required Health Endpoints

- `/health` — readiness probe
- `/heartbeat` — liveness probe

---

## Restart Policies

All business agents: `restart: unless-stopped`

---

## Autonomy Levels

| Level | Description | Status |
|-------|-------------|--------|
| **Level 1** | Manual operator approval | — |
| **Level 2** | Task execution autonomy | **CURRENT** |
| **Level 3** | Workflow autonomy | — |
| **Level 4** | Inter-agent delegation | — |
| **Level 5** | Self-healing infrastructure | NOT recommended yet |

**Current: Level 2** — Do NOT allow unrestricted shell execution, unrestricted deployment, recursive self-modification, or autonomous governance edits yet.

---

## Host File Structure

```
/home/aiops/
├── leo/                    # LEO root workspace
├── agents/
│   ├── vss/               # VSS agent persistent storage
│   ├── qenix/             # (future)
│   ├── panaceax/          # (future)
│   └── research/          # (future)
├── observability/          # Grafana, Prometheus, Loki
├── governance/             # Global governance policies
└── backups/               # Backup storage
```

### VSS Agent Files

```
/home/aiops/agents/vss/
├── memory/
├── logs/
├── governance/
├── tasks/
├── audits/
├── workflows/
├── prompts/
├── sessions/
└── backups/
```

---

## Root Cause Lesson

> **ROOTAI = CONTROL PLANE**  
> **Business agents = DATA PLANE**
>
> This separation is CRITICAL. Never merge them again. That was the exact root cause of the VSustain contamination incident.

---

## Implementation Order

| Phase | Task | Priority |
|-------|------|----------|
| 1 | Stabilize LEO | ✅ |
| 2 | Finalize provider auth | 🔄 |
| 3 | Validate Telegram routing | 🔄 |
| 4 | Create isolated VSS container | 📋 |
| 5 | Create governance files | 📋 |
| 6 | Create memory federation | 📋 |
| 7 | Add observability exporters | 📋 |
| 8 | Add browser workers | 📋 |
| 9 | Add workflow execution layer | 📋 |
| 10 | Add inter-agent delegation | 📋 |

---

*Architecture v3 — LEO — 2026-05-25*  
*Root cause: previous runtime contamination*  
*Fix: complete isolation, memory federation, strict permission boundaries*
