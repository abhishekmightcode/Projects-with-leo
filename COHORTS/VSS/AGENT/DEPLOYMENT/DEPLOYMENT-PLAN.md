# VSS Sub-Agent — Deployment Plan (v3)

**Version:** 3.0  
**Date:** 2026-05-25  
**Updated by:** LEO  

---

## Prerequisites

Before starting, ensure:
- [ ] Docker and Docker Compose installed on AIforce host
- [ ] `openclaw:latest` image available (or to be pulled)
- [ ] VSS Telegram bot token ready (`@VSustainAIbot`)
- [ ] LEO is stabilized and operational
- [ ] Provider auth finalized

---

## Implementation Phases

### Phase 1: Host Preparation (Steps 1–3)

#### STEP 1 — Create Container Directory

```bash
mkdir -p ~/agents/vss
mkdir -p ~/agents/vss/memory
mkdir -p ~/agents/vss/logs
mkdir -p ~/agents/vss/governance
mkdir -p ~/agents/vss/tasks
mkdir -p ~/agents/vss/audits
mkdir -p ~/agents/vss/workflows
mkdir -p ~/agents/vss/prompts
mkdir -p ~/agents/vss/sessions
mkdir -p ~/agents/vss/backups
```

**Directory purpose:**

| Directory | Purpose |
|-----------|---------|
| `memory/` | Customer data, learning, context |
| `logs/` | Action logs, conversation logs, anomaly logs |
| `governance/` | identity.md, rules.md, permissions.md, escalations.md |
| `tasks/` | Pending tasks, task queue |
| `audits/` | Audit records for LEO review |
| `workflows/` | Reusable workflow templates |
| `prompts/` | System prompts, response templates |
| `sessions/` | Session state and history |
| `backups/` | Backup snapshots |

---

#### STEP 2 — Create Docker Network

```bash
docker network create agent-network
```

This network isolates all agent containers from other host traffic while allowing shared infrastructure access.

---

#### STEP 3 — Create VSS PostgreSQL Schema

Connect to `leo_memory` database and create isolated VSS schema:

```sql
CREATE SCHEMA IF NOT EXISTS vss;

-- Customers table
CREATE TABLE IF NOT EXISTS vss.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interactions table
CREATE TABLE IF NOT EXISTS vss.interactions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES vss.customers(id),
    type VARCHAR(50), -- call, whatsapp, meeting
    direction VARCHAR(10), -- inbound, outbound
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE IF NOT EXISTS vss.tasks (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES vss.customers(id),
    description TEXT NOT NULL,
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit table
CREATE TABLE IF NOT EXISTS vss.audit (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Phase 2: Redis Namespace (Step 4)

#### STEP 4 — Create VSS Redis Namespace

Set up isolated Redis namespace for VSS (done via application config, not Redis MULTI):

```
vss:sessions    → session data
vss:memory      → short-term memory
vss:tasks       → task queue state
vss:state       → agent runtime state
vss:cache       → cached lookups
```

Configure in OpenClaw profile or agent startup:

```bash
# In agent environment or config
REDIS_NAMESPACE=vss
```

---

### Phase 3: Container Creation (Steps 5–6)

#### STEP 5 — Create Docker Compose Service

Create `/home/aiops/agents/vss/docker-compose.yml`:

```yaml
version: '3.8'

services:
  vss-agent:
    image: openclaw:latest
    container_name: vss-agent
    restart: unless-stopped
    environment:
      TELEGRAM_BOT_TOKEN: ${VSS_TELEGRAM_TOKEN}
      OPENCLAW_PROFILE: vss
      REDIS_NAMESPACE: vss
      POSTGRES_SCHEMA: vss
      DATABASE_URL: postgres://${PG_USER}:${PG_PASSWORD}@host.docker.internal:5432/leo_memory
      REDIS_URL: redis://host.docker.internal:6379
    volumes:
      - /home/aiops/agents/vss:/workspace
    networks:
      - agent-network
    ports:
      - "18801:18789"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  agent-network:
    external: true
```

---

#### STEP 6 — Initialize Isolated OpenClaw Profile

Inside the container (first run or via exec):

```bash
# Create isolated profile
openclaw --profile vss init

# Start gateway with isolated profile
openclaw --profile vss gateway
```

This prevents:
- Session contamination from other agents
- Config pollution between profiles
- Telegram routing overlap

---

### Phase 4: Governance Setup (Steps 7–8)

#### STEP 7 — Create Governance Files

Create at `/home/aiops/agents/vss/governance/`:

**`identity.md`:**
```markdown
# VSS Agent Identity

**Name:** PraveshAgent
**Role:** VSS Field Sales AI Assistant
**Owner:** Mr. Pravesh Kumar Tiwari
**Supervisor:** LEO (Root Orchestrator)
**Telegram:** @VSustainAIbot

## Purpose
Handle day-to-day VSS sales operations: customer communication,
price quotes, follow-ups, CRM updates.

## Boundaries
- Cannot modify host infrastructure
- Cannot access other agent memory
- Must escalate deletions to LEO
- Must report anomalies to LEO
```

**`rules.md`:**
```markdown
# VSS Agent Rules

## Core Rules
1. Pravesh talks to agent via Telegram ONLY
2. Agent talks to customers via WhatsApp ONLY (on Pravesh's command)
3. All customer data stays in VSS schema/namespace
4. All actions logged to audit table
5. LEO reviews logs daily

## Permission Boundaries
- CAN: send WhatsApp, update CRM, create tasks, lookup contacts
- CANNOT: delete records, modify infra, access other agents
- MUST: escalate deletions, report anomalies, log all actions

## Response Requirements
- Always confirm actions to Pravesh
- Quote prices clearly with terms
- Log before executing external actions
```

**`permissions.md`:**
```markdown
# VSS Agent Permissions

## Allowed Actions
| Action | Scope | Requires Approval |
|--------|-------|-------------------|
| Send WhatsApp | Customer list | No |
| Update CRM | Own schema only | No |
| Create task | VSS tasks | No |
| Lookup contact | Google Contacts | No |
| Generate quote | Internal templates | No |

## Blocked Actions
| Action | Reason |
|--------|--------|
| Delete customer | LEO approval required |
| Delete interaction | LEO approval required |
| Modify infra | Never allowed |
| Access other schemas | Forbidden |
| Shell commands | Forbidden |

## Escalation Triggers
- DELETE requests → pause → LEO approval
- Unknown package install → block → LEO notification
- VM/host access attempt → block → LEO incident log
- >500 messages/hour → rate limit → LEO alert
```

**`escalations.md`:**
```markdown
# VSS Agent Escalation Matrix

## Immediate Escalation (→ LEO NOW)
- Customer delete request
- Data deletion of any kind
- Suspicious behavior detected
- Unauthorized access attempt
- System integrity issue

## Deferred Escalation (→ LEO within 1 hour)
- Anomaly pattern detected
- Unusual timing patterns
- Failed automation recovery
- New external service intent

## Routine Reports (→ LEO daily)
- Daily action summary
- Task completion report
- Anomaly log review
- Health status

## Escalation Format
```
ESCALATION: [TYPE]
Agent: vss-agent
Time: [timestamp]
Details: [description]
Action Taken: [if any]
Required Response: [yes/no]
```
```

---

#### STEP 8 — Create Governance Archive

```bash
cd /home/aiops/agents/vss/governance
tar -czf governance-backup-$(date +%Y%m%d).tar.gz *.md
```

---

### Phase 5: Observability Setup (Step 9)

#### STEP 9 — Configure Health Checks and Logging

Ensure agent exports:

**Health endpoint:** `GET /health` → returns `{"status": "ok"}`

**Heartbeat:** Every 60 seconds to Uptime Kuma

**Log shipping:** All logs to Loki via Promtail or direct shipper

```yaml
# Add to docker-compose.yml under vss-agent
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### Phase 6: Validation (Steps 10–12)

#### STEP 10 — Validate Telegram Routing

```bash
# Test bot is responding
curl -s "https://api.telegram.org/bot${VSS_TELEGRAM_TOKEN}/getMe"
```

Then manually test: send message to @VSustainAIbot — should respond.

---

#### STEP 11 — Validate Database Connection

```bash
# Inside container
psql "$DATABASE_URL" -c "SELECT 1 FROM vss.customers LIMIT 1;"
```

Should return `1` without error.

---

#### STEP 12 — Validate Redis Namespace

```bash
# Inside container
redis-cli -u "$REDIS_URL" SELECT 1  # if using separate DB, or
redis-cli -u "$REDIS_URL" KEYS "vss:*"
```

Should show `vss:*` keys only.

---

## Deployment Checklist

### Pre-Deployment
- [ ] Docker network `agent-network` exists
- [ ] PostgreSQL schema `vss` created with tables
- [ ] Redis namespace `vss:*` configured
- [ ] Telegram bot token in `.env` or secrets manager
- [ ] Governance files created
- [ ] OpenClaw image available

### Deployment
- [ ] `docker-compose up -d vss-agent`
- [ ] Container started and healthy
- [ ] Telegram bot responding to test message
- [ ] Database connection verified
- [ ] Redis connection verified

### Post-Deployment
- [ ] First interaction logged
- [ ] LEO can read VSS audit logs
- [ ] Uptime Kuma shows agent healthy
- [ ] Pravesh introduced to bot
- [ ] First test quote sent

---

## Rollback Procedure

```bash
# Stop container (preserves logs/data)
docker-compose down

# Restore previous version
docker-compose pull
docker-compose up -d

# Full reset (nuclear)
docker-compose down -v  # WARNING: deletes volumes
# Only if data loss is acceptable
```

---

## Current Status

| Phase | Status |
|-------|--------|
| Phase 1: Host Preparation | 📋 Pending |
| Phase 2: Redis Namespace | 📋 Pending |
| Phase 3: Container Creation | 📋 Pending |
| Phase 4: Governance Setup | 📋 Pending |
| Phase 5: Observability | 📋 Pending |
| Phase 6: Validation | 📋 Pending |

---

*Deployment Plan v3 — LEO — 2026-05-25*
