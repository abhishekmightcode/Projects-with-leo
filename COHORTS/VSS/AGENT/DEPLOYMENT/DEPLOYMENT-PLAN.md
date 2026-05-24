# VSS Sub-Agent — Deployment Plan

**Project:** VSS Pravesh AI Agent  
**Type:** Containerized Sub-Agent  
**Parent:** LEO (Root Orchestrator)  
**Date:** 2026-05-24

---

## Deployment Options Compared

| Option | OpenClaw Managed | Own Container | Hermes Involved |
|--------|-----------------|---------------|-----------------|
| **Option A: OpenClaw Sub-Agent** | ✅ Yes | ❌ No | ❌ No |
| Option B: OpenClaw + Hermes | ✅ Yes | ❌ No | ✅ Yes |
| **Option C: Docker + OpenClaw (Recommended)** | Partial | ✅ Yes | ❌ No |
| Option D: Pure Docker + API | ❌ No | ✅ Yes | Optional |

### Recommendation: **Option C — Docker + OpenClaw Hybrid**

**Why not Option A (pure OpenClaw sub-agent)?**
- OpenClaw sub-agents run as isolated sessions but share the same host process
- No separate container means no isolated memory store, no independent healthcheck
- Credentials would need to be shared at host level

**Why not Option D (pure Docker)?**
- You'd lose OpenClaw's session management, tool routing, and Telegram integration
- More ops overhead for Abhishek to manage

**Why Option C is best:**
- vsustain-agent runs in its own Docker container
- OpenClaw manages the session lifecycle via `sessions_spawn`
- Pravesh talks to the agent via Telegram (through LEO or directly)
- Agent has its own Redis + Postgres for isolated memory
- LEO supervises and can audit all agent actions

---

## Phase 1: Infrastructure Setup (Week 1)

### 1.1 Create Agent Workspace
```bash
mkdir -p /home/aiops/leo/agents/vsustain/{workspace/{context,memory/customers,plans/pending,credentials},tools,logs}
```

### 1.2 Create Docker Compose Stack
```yaml
# vsustain-stack.yml
services:
  vsustain-agent:
    build:
      context: /home/aiops/leo/agents/vsustain
      dockerfile: Dockerfile.agent
    container_name: vsustain-agent
    env_file: /home/aiops/leo/agents/vsustain/.env.vss
    depends_on:
      vsustain-redis:
        condition: service_healthy
      vsustain-postgres:
        condition: service_healthy
    restart: unless-stopped
    memory_limit: 1GB
    networks:
      - vsustain-net

  vsustain-redis:
    image: redis:7-alpine
    container_name: vsustain-redis
    volumes:
      - vsustain-redis-data:/data
    restart: unless-stopped
    networks:
      - vsustain-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  vsustain-postgres:
    image: postgres:16-alpine
    container_name: vsustain-postgres
    environment:
      POSTGRES_DB: vsustain
      POSTGRES_USER: pravesh
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    volumes:
      - vsustain-pg-data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - vsustain-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pravesh"]
      interval: 30s
      timeout: 10s
      retries: 3

  vsustain-browser:
    image: ghcr.io/browserless/chromium:latest
    container_name: vsustain-browser
    ports:
      - "9223:9222"
    restart: unless-stopped
    networks:
      - vsustain-net

volumes:
  vsustain-redis-data:
  vsustain-pg-data:

networks:
  vsustain-net:
    driver: bridge
```

### 1.3 Create Dockerfile
```dockerfile
FROM node:18-alpine

# Install Python + whisper deps
RUN apk add --no-cache python3 ffmpeg

# Install whisper (CPU only)
RUN pip install --no-cache-dir openai-whisper torch

WORKDIR /app

# Copy agent workspace
COPY workspace/ ./workspace/

# Entrypoint
CMD ["node", "/app/agent-runner.js"]
```

### 1.4 Create Agent Config
```yaml
# agent-config.yml
agent_id: vsustain
agent_name: Pravesh
role: vss-field-sales-assistant
parent: leo
cohort: VSS

memory:
  type: hybrid  # redis + file
  redis:
    host: vsustain-redis
    port: 6379
    db: 0
  file:
    path: /app/workspace/memory

tools:
  - whatsapp-sender
  - zoho-crm-client
  - price-quotation-gen
  - task-scheduler
  - google-contacts
  - google-messages
  - web-search

limits:
  max_concurrent_tasks: 3
  max_daily_messages: 500
  require_leo_approval_for:
    - new_automation
    - new_workflow
    - crm_schema_change

language:
  primary: hi  # Hindi
  fallback: en  # English
  mixed: true   # Can switch mid-conversation
```

---

## Phase 2: Integration Setup (Week 2)

### 2.1 WhatsApp Integration
- Option A: WhatsApp Business API (official, paid)
- Option B: n8n WhatsApp webhook (more flexible)
- Option C: wa-js (browser automation for WhatsApp Web)
- **Recommendation:** Start with n8n webhook → most flexible for Pravesh's use case

### 2.2 Zoho CRM Setup
- Create VSS API credentials in Zoho Developer Console
- Store in `.env.vss`
- Test connection with read/write access to UPS module

### 2.3 Google Integration
- Google Contacts API (read-only for customer lookup)
- Google Messages API (if available in India) — or fallback to SMS

---

## Phase 3: Agent Development (Week 3-4)

### 3.1 Core Capabilities (Priority Order)

1. **Price Quotation Generator**
   - Input: customer name, products, quantities
   - Output: formatted WhatsApp message with pricing
   - Template-based with VSS branding

2. **Follow-up Message Scheduler**
   - Daily follow-up list from CRM
   - Scheduled WhatsApp messages at set times
   - Track delivery status

3. **CRM Query Handler**
   - "Show me today's meetings"
   - "Who are my pending follow-ups"
   - "Add notes to dealer X"

4. **Task Reminder System**
   - "Remind me to call customer X tomorrow"
   - "Create follow-up for dealer Y"
   - "Set reminder for 3pm"

5. **Market Research**
   - "What's the price of 5kW solar panel"
   - "Who is Luminous's competitor"
   - "Latest solar subsidy news"

### 3.2 Voice Command Pipeline
```
Pravesh voice note → Telegram → OpenClaw → LEO routes to → vsustain-agent
                                                              │
                                                     Whisper STT
                                                              │
                                                     Parse intent
                                                              │
                                                     Execute action
                                                              │
                                                     Respond via WhatsApp/Telegram
```

---

## Phase 4: Testing & Deployment (Week 5)

### 4.1 Testing Checklist
- [ ] WhatsApp message delivery (price quote)
- [ ] WhatsApp message delivery (follow-up)
- [ ] Zoho CRM read (dealer list)
- [ ] Zoho CRM write (dealer meets entry)
- [ ] Google Contacts lookup
- [ ] Task scheduling (cron)
- [ ] Voice note → action pipeline
- [ ] LEO supervision loop (agent → LEO → approval)

### 4.2 Go-Live Steps
1. Deploy vsustain-stack on VM
2. Register Pravesh's phone as test user
3. Run 1-week pilot with Abhishek monitoring
4. Train Pravesh on voice commands
5. Full rollout

---

## Rollback Plan

| Failure | Rollback Action |
|---------|----------------|
| Agent crashes | Docker auto-restart (`unless-stopped`) |
| Redis data lost | Data persists in `vsustain-redis-data` volume |
| Postgres data lost | Data persists in `vsustain-pg-data` volume |
| WhatsApp integration fails | Fallback to Telegram-only for Pravesh |
| Zoho fails | Agent queues actions, retries with backoff |
| Full compromise | Kill container → LEO takes over Pravesh tasks manually |

---

## Estimated Cost

| Resource | Cost |
|----------|------|
| Additional RAM (2GB more) | ~₹500/month on Azure |
| WhatsApp Business API | ₹200-500/month |
| n8n cloud (if not self-hosted) | ₹0-500/month |
| Zoho CRM (already have) | existing |

**Total additional cost:** ~₹500-1000/month

---

*Deployment Plan v1.0 — LEO — 2026-05-24*