# VSS Sub-Agent — Deployment Plan (v2)

**Version:** 2.0  
**Date:** 2026-05-24  
**Updated by:** LEO

---

## What's Different in v2

- **Telegram first** — Pravesh talks to agent on Telegram, not WhatsApp
- **Immediate test** — Abhishek tests now, Pravesh gets it later after training
- **Learning agent** — adapts through every conversation
- **LEO approval only on sensitive ops** — not on routine actions

---

## Deployment Option: Option C (Docker + OpenClaw Hybrid)

### Why Option C
- vsustain-agent runs in **its own Docker container** → isolated, own memory
- OpenClaw manages the **session lifecycle** via `sessions_spawn`
- Pravesh talks to the agent via **Telegram bot** (his phone)
- Agent has **own Redis + Postgres** for isolated memory
- LEO **supervises** via log review — not always in the loop
- Agent **learns** through each conversation

### Why NOT Option A (OpenClaw sub-agent only)
- No separate container → no isolated memory store
- Credentials shared at host level → security risk
- No independent healthcheck → Pravesh's agent crashes affect others

### Why NOT Option D (pure Docker)
- Lose OpenClaw's session management, tool routing, Telegram integration
- More ops overhead for Abhishek

---

## Phase 0: Telegram Bot Live (THIS WEEK) — PRIORITY

**Goal:** Abhishek tests the agent on Telegram immediately. No external integrations yet.

### Step 0.1: Create PraveshAgent Telegram Bot

Abhishek needs to:
1. Open Telegram → chat with **@BotFather**
2. Send `/newbot`
3. Name: `VSS Pravesh Agent` (or whatever Pravesh prefers)
4. Username: `<something>_bot` (must end in `bot`)
5. Copy the **bot token** (format: `123456789:ABCdef...`)
6. Share the token with LEO

### Step 0.2: Create Agent Workspace

```bash
mkdir -p /home/aiops/leo/agents/vsustain/workspace/{context,memory/daily,memory/customers,memory/pravesh-profile,plans/pending,logs/actions,logs/conversations,credentials}
```

### Step 0.3: Create Credentials File

```bash
# /home/aiops/leo/agents/vsustain/.env.vss
TELEGRAM_BOT_TOKEN=your_bot_token_here
VSS_ZOHO_TOKEN=your_zoho_token_here
VSS_ZOHO_DC=in
WHATSAPP_API_KEY=your_whatsapp_key_here
GOOGLE_CONTACTS_CLIENT_ID=your_google_client_id
GOOGLE_CONTACTS_CLIENT_SECRET=your_google_secret
# PostgreSQL for vsustain
POSTGRES_DB=vsustain
POSTGRES_USER=pravesh
POSTGRES_PASSWORD=secure_password_here
```

### Step 0.4: Deploy Container

```bash
cd /home/aiops/leo/agents/vsustain
docker-compose -f vsustain-stack.yml up -d
```

### Step 0.5: Abhishek Tests

Abhishek messages the PraveshAgent bot and:
- Introduces Pravesh (name, business, style)
- Shares context about VSS
- Tests basic commands
- Agent learns and adapts

### Step 0.6: Refine & Train

Based on test conversations:
- LEO reviews logs
- LEO trains agent on Pravesh's personality
- Agent's responses refined

### Step 0.7: Hand to Pravesh

- Pravesh gets the bot username
- Abhishek monitors for 1 week
- Refine based on real usage

---

## Phase 1: Zoho + Contacts Integration (Week 1-2)

After Phase 0 is stable:

### 1.1 Zoho CRM
- Create VSS API credentials at `crm.zoho.in`
- Add to `.env.vss`
- Test: agent can read dealer list, update records
- Log all Zoho operations

### 1.2 Google Contacts
- Create Google Cloud project → Contacts API enabled
- OAuth credentials → add to `.env.vss`
- Test: "find Amit" → returns number + email
- Agent stores found contacts in `memory/customers/`

### 1.3 Train on Customer Data
- Upload existing customer list (if any)
- Agent learns names, numbers, preferences
- Stored in `memory/customers/`

---

## Phase 2: WhatsApp Customer Send (Week 3-4)

After Phase 1 is stable:

### 2.1 WhatsApp Integration
- Option A: WhatsApp Business API (official)
- Option B: n8n WhatsApp webhook
- Option C: wa-js (WhatsApp Web automation)
- **Recommendation:** Start with n8n webhook → most flexible

### 2.2 Price Quote Template
- VSS product list + pricing
- Template for WhatsApp messages
- Agent generates on command

### 2.3 Test Customer Flow
- Pravesh: "send to Rajesh about 5kVA"
- Agent: Google Contacts → Rajesh → WhatsApp → done
- Log action

---

## Phase 3: Full Autonomy + Learning (Week 5+)

- Agent operates independently
- LEO reviews logs daily
- Learns from every interaction
- Adapts to Pravesh's style

---

## Docker Compose (Full Stack)

```yaml
# vsustain-stack.yml (complete)

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
    volumes:
      - /home/aiops/leo/agents/vsustain/workspace:/app/workspace

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
      POSTGRES_PASSWORD: ${PG_PASSWORD}
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

---

## Dockerfile

```dockerfile
# Dockerfile.agent
FROM node:18-alpine

# Install Python + ffmpeg (for Whisper)
RUN apk add --no-cache python3 ffmpeg

# Install Whisper + torch (CPU only)
RUN pip install --no-cache-dir openai-whisper torch

# Copy workspace
COPY workspace/ /app/workspace/

# Set working dir
WORKDIR /app

# Entrypoint — runs OpenClaw agent session
CMD ["node", "/app/agent-runner.js"]
```

---

## What Abhishek Needs to Provide NOW

| Item | How to Get | Status |
|------|-----------|--------|
| **Telegram Bot Token** | @BotFather → /newbot | ⏳ NEED NOW |
| Zoho API Token | crm.zoho.in → Developer Console | ⏳ Needed in Week 1 |
| WhatsApp approach | Business API / n8n / wa-js | ⏳ Needed in Week 2 |
| Google Contacts credentials | Google Cloud Console | ⏳ Needed in Week 2 |
| VSS product list | Share with LEO | ⏳ Needed in Week 3 |

**Without bot token → can't deploy.**

---

## Rollback Plan

| Failure | Rollback |
|---------|----------|
| Agent crashes | Docker auto-restart (`unless-stopped`) |
| Redis data lost | Persistent volume → restored |
| Postgres data lost | Persistent volume → restored |
| WhatsApp fails | Telegram-only operation continues |
| Zoho fails | Agent queues → retries → LEO notified |
| Full compromise | Kill container → LEO takes over manually |

---

## RAM Calculation

| Component | RAM |
|-----------|-----|
| vsustain-agent (OpenClaw session + tools) | 512 MB |
| vsustain-redis | 256 MB |
| vsustain-postgres | 512 MB |
| vsustain-browser (chromium) | 256 MB |
| Whisper STT (during voice transcribe) | +400 MB |
| **Total peak** | **~1.9 GB** |
| **Currently used** | ~2.1 GB |
| **Free** | ~5.7 GB available |

**Actually — we have enough RAM.** Current system has 7.8 GB total, ~5.7 GB available. No extra RAM needed. The earlier estimate was conservative. Agent will run fine.

---

*Deployment Plan v2 — LEO — 2026-05-24*