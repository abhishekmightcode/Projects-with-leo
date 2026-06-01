# 🤖 AIforce Infrastructure Audit Report
**Generated:** 2026-06-01 12:33 UTC
**Host:** AIforce
**Uptime:** 11 days, 14 hours
**Auditor:** LEO 🦁

---

## 1. SERVER OVERVIEW

| Property | Value |
|---|---|
| **Hostname** | `AIforce` |
| **OS** | Ubuntu 24.04 LTS |
| **Kernel** | Linux 6.17.0-1013-azure |
| **CPU** | AMD EPYC 7763 64-Core (2 vCPUs allocated) |
| **RAM** | 7.8 GB total · 3.9 GB used · 3.8 GB available |
| **Swap** | 4 GB total · 1.8 GB used |
| **Disk** | 61 GB total · 44 GB used (73%) · 18 GB free |
| **Architecture** | x86_64 Azure VM |
| **Container Runtime** | Docker (both `aiops` and `AIforce` users in docker group) |

---

## 2. USERS & PERMISSIONS

| User | Home | Groups | Notes |
|---|---|---|---|
| `root` | `/root` | root | System administrator |
| `AIforce` | `/home/AIforce` | sudo, docker | Primary sudo user |
| `aiops` | `/home/aiops` | docker | OpenClaw / agent runtime user |

---

## 3. CONTAINER INVENTORY

```
┌──────────────┬────────────────────────────────┬────────┬───────────────────────┬──────────────────────────────────┐
│ CONTAINER    │ IMAGE                          │ STATUS │ PORTS                  │ PURPOSE                          │
├──────────────┼────────────────────────────────┼────────┼───────────────────────┼──────────────────────────────────┤
│ vss-agent    │ vss-vss-agent (local build)   │ Up 5d  │ 18801→18789/tcp        │ VSustainAI agent (isolated)      │
│ stt-service  │ stt-stt-service (local build) │ Up 5d  │ 9001/tcp               │ Speech-to-text service           │
│ leo-browser  │ ghcr.io/browserless/chromium  │ Up 6d  │ 9222/tcp               │ Browser automation (⚠️ broken)   │
│ leo-uptime   │ louislam/uptime-kuma           │ Up 6d  │ 3001/tcp               │ Uptime monitoring                │
│ leo-grafana  │ grafana/grafana               │ Up 7d  │ 3000/tcp               │ Metrics dashboards               │
│ leo-prometheus│ prom/prometheus               │ Up 7d  │ 9090/tcp               │ Metrics collection               │
│ leo-postgres │ postgres:16                    │ Up 7d  │ 5432/tcp (localhost)   │ Database (⚠️ no active consumer)│
│ leo-redis    │ redis:7                        │ Up 7d  │ 6379/tcp               │ Cache/queue (⚠️ no active consumer│
└──────────────┴────────────────────────────────┴────────┴───────────────────────┴──────────────────────────────────┘
```

### Docker Disk Usage
- **Images:** 28.92 GB (8 images)
- **Containers:** 11.9 GB (8 containers)
- **Volumes:** 4 local volumes (101 MB used)
- **Build cache:** 7.6 GB total · 2.1 GB reclaimable

---

## 4. DOCKER NETWORKS

| Network | Subnet | Connected Containers | Notes |
|---|---|---|---|
| `bridge` | 172.17.0.0/16 | leo-postgres, leo-redis | Default bridge |
| `agent-network` | 172.23.0.0/16 | _(empty)_ | Shared infra network |
| `stt_default` | 172.25.0.0/16 | stt-service, vss-agent | STT + VSS agent |
| `vss_default` | 172.24.0.0/16 | vss-agent | VSS isolated network |
| `leo-observability` | 172.x.x.x/16 | leo-uptime, leo-grafana, leo-prometheus | Monitoring stack |
| `leo-browser` | 172.x.x.x/16 | leo-browser | Browser container |
| `hermes-network` | 172.x.x.x/16 | _(empty)_ | ⚠️ HERMES PREPARED — no container yet |
| `ai-network` | 172.x.x.x/16 | — | Isolated AI network |
| `leo-cognition` | 172.x.x.x/16 | — | Cognition services |
| `host` | — | — | Host network mode |
| `none` | — | — | No network mode |

---

## 5. AGENT ARCHITECTURE

### 5.1 LEO (Host Process — Root AI) 🦁

| Property | Value |
|---|---|
| **Runtime** | OpenClaw host process (`openclaw`) |
| **OpenClaw Version** | 2026.5.22 (commit a374c3a) |
| **Config** | `/home/aiops/.openclaw/openclaw.json` |
| **Workspace** | `/home/aiops/.openclaw/workspace/` |
| **Memory** | `/home/aiops/.openclaw/workspace/MEMORY.md` |
| **Telegram Bot** | `@Chotarajandonbot` (token: `894351…zv5c`) |
| **Model** | MiniMax-M2.7 via minimax-portal (OAuth) |
| **Auth Profile** | `minimax-portal:default` → `/home/aiops/.openclaw/agents/main/agent/auth-profiles.json` |
| **Skills** | System skills at `/usr/lib/node_modules/openclaw/skills/` |
| **Channels** | Telegram (configured) |

**LEO Workspace Structure:**
```
workspace/
├── VSS/                    (legacy VSS materials — pre-agent era, 112KB)
├── agents/                 (⚠️ vsustain workspace EMPTY/ORPHANED)
├── google-credentials/     (OAuth token management)
│   ├── token.json          (refresh token)
│   └── token_manager.py
├── skills/                 (custom skills)
├── memory/                 (daily session memory)
│   ├── 2026-05-26.md
│   ├── 2026-05-27.md
│   └── heartbeat-state.json
├── TOKENS_GOOGLE.json
├── bangalore_colleges_data.md
├── bangalore_iti_colleges.json
├── bangalore_polytechnic_colleges.json
├── jayanagar_service_apartments.json
├── HEARTBEAT.md, IDENTITY.md, SOUL.md, AGENTS.md, TOOLS.md, USER.md, MEMORY.md
└── docs/
```

> ⚠️ **Orphaned Workspace:** `/home/aiops/.openclaw/agents/vsustain/` is empty — remnant from old architecture. Active VSS workspace is at `/home/aiops/agents/vss/`.

---

### 5.2 VSustainAI (vss-agent container) ☀️

| Property | Value |
|---|---|
| **Container** | `vss-agent` |
| **Image** | `vss-vss-agent` (built locally from Node:24-bookworm) |
| **Created** | 2026-05-26T13:18:50Z |
| **Runtime** | OpenClaw inside Node:24 container |
| **Workspace** | `/home/aiops/agents/vss/` (bind-mounted to `/workspace` inside container) |
| **Config Inside** | `/root/.openclaw-vss/openclaw.json` (separate from host LEO config) |
| **Governance** | `/workspace/governance/` → identity.md, rules.md, permissions.md, escalations.md |
| **Memory** | `/workspace/memory/identity.md` |
| **Telegram Bot** | `@VSustainAIbot` (token: `862563…lv34`) |
| **Networks** | `stt_default` (172.25.0.3), `vss_default` (172.24.0.2) |
| **STT Endpoint** | `http://host.docker.internal:9001/transcribe` |
| **WhatsApp** | DoubleTick API — WABA: `919900108067` |
| **Zoho MCP** | ⚠️ Signup pending at https://www.zoho.com/mcp/signup.html |

**vss-agent Workspace Structure:**
```
agents/vss/
├── openclaw-config/         (separate OpenClaw config — /root/.openclaw-vss/)
│   ├── openclaw.json
│   └── openclaw.json.bak.*
├── governance/
│   ├── identity.md          (VSustainAI ☀️)
│   ├── rules.md             (WhatsApp/STT operational rules)
│   ├── permissions.md
│   └── escalations.md
├── memory/
│   └── identity.md
├── prompts/
│   ├── system.md
│   ├── ZOHO_MCP_KNOWLEDGE_BASE.md
│   └── ZOHO_MCP_LEARN.md
├── mcp-server/              (Node.js MCP server)
│   ├── package.json         (@macnishio/zoho-mcp-server v1.2.26)
│   └── node_modules/
├── skills/
│   ├── stt/                 (STT processor module)
│   └── whatsapp/            (DoubleTick client, workflows, templates)
├── integrations/
│   └── doubletick.py        (DoubleTick WhatsApp integration)
├── zoho-config.json         (new credentials)
├── docker-compose.yml
├── Dockerfile               (FROM node:24-bookworm)
└── AGENTS.md, BOOTSTRAP.md, IDENTITY.md, MEMORY.md, SOUL.md, TOOLS.md
```

**Governance Rules (from rules.md):**
- **WhatsApp:** MUST use `skills.whatsapp` module (NOT native `message` tool — will route incorrectly)
- **STT:** Use `skills.stt.processor` at `http://host.docker.internal:9001/transcribe`
- **Escalation:** Route to ROOTAI (LEO) for infrastructure issues, cross-agent coordination

---

## 6. SHARED SERVICES

| Service | Port | Container | Status | Consumers |
|---|---|---|---|---|
| **PostgreSQL** | 5432 (localhost only) | leo-postgres | Up 7d | ⚠️ None — no consumers configured |
| **Redis** | 6379 | leo-redis | Up 7d | ⚠️ None — unused |
| **STT Service** | 9001 | stt-service | Up 5d | ✅ vss-agent (active — logs confirm usage) |
| **Uptime Kuma** | 3001 | leo-uptime | Up 6d (healthy) | Browser UI |
| **Grafana** | 3000 | leo-grafana | Up 7d | Browser UI |
| **Prometheus** | 9090 | leo-prometheus | Up 7d | ⚠️ No targets configured — not scraping anything |
| **Browserless Chrome** | 9222 | leo-browser | Up 6d | ⚠️ BROKEN — debug port not responding |

### STT Service Details
- **Base image:** Python 3.11 + FastAPI
- **Health:** `GET /` returns 200 OK · `GET /health` returns **404** (broken monitoring)
- **Active usage:** vss-agent (172.25.0.3) actively transcribing — logs show continuous POST /transcribe
- **Health endpoint issue:** STT logs show repeated `GET /health HTTP/1.1" 404` — monitoring will fail

---

## 7. MODEL PROVIDER AUTHENTICATION

**MiniMax OAuth (LEO host):**
```json
{
  "profile": "minimax-portal:default",
  "type": "oauth",
  "provider": "minimax-portal",
  "expires": 1811264709205  (≈ May 2027)
}
```
- **Location:** `/home/aiops/.openclaw/agents/main/agent/auth-profiles.json`
- **Also available:** `minimax:global` (api_key type)

---

## 8. TELEGRAM BOTS

| Bot | Token (masked) | Linked Agent | Purpose |
|---|---|---|---|
| `@Chotarajandonbot` | `894351…zv5c` | LEO (host process) | Root AI orchestrator |
| `@VSustainAIbot` | `862563…lv34` | VSustainAI (vss-agent) | Solar CRM/operations |

---

## 9. WHATSAPP INTEGRATION

**Provider:** DoubleTick
- **API Key:** `key_RueP4Mjgc6knJL…` (full key in `doubletick.py`)
- **WABA Number:** `919900108067` (91 + 9900108067, no + prefix)
- **Base URL:** `https://public.doubletick.io`
- **Files:**
  - `/home/aiops/.openclaw/workspace/VSS/integrations/doubletick.py` (legacy)
  - `/home/aiops/agents/vss/integrations/doubletick.py` (active — in vss-agent workspace)

**Available Templates:**
| Template | Variables | Use Case |
|---|---|---|
| `chat_support` | 1 (name) | Follow-ups, reminders |
| `invoice` | 3 (ID, date, GST) | Invoice images |
| `invoice_pdf` | 0 | PDF proposals/documents |

---

## 10. ZOHO MCP INTEGRATION

| Property | Value |
|---|---|
| **Status** | ⚠️ INCOMPLETE — signup pending |
| **Config File** | `/home/aiops/agents/vss/zoho-config.json` |
| **Client ID** | `1000.GRI56LMPI3FQGQBZYK7UG2C49XUSDB` |
| **API Domain** | `https://www.zohoapis.in` |
| **Scope** | `ZohoCRM.modules.ALL` |
| **MCP Server** | `/home/aiops/agents/vss/mcp-server/` |
| **MCP Package** | `@macnishio/zoho-mcp-server` v1.2.26 (Node.js) |
| **Knowledge Base** | `/home/aiops/agents/vss/prompts/ZOHO_MCP_KNOWLEDGE_BASE.md` |
| **Learning Doc** | `/home/aiops/agents/vss/prompts/ZOHO_MCP_LEARN.md` |
| **Signup URL** | https://www.zoho.com/mcp/signup.html |
| **Action Required** | Abhishek must complete Zoho MCP signup |

---

## 11. FILESYSTEM MAP

```
/home/
├── AIforce/                    (user: AIforce, sudo + docker group)
│
├── aiops/                      (user: aiops, docker group)
│   ├── agents/
│   │   └── vss/               (VSustainAI workspace — ACTIVE)
│   │       ├── governance/     (identity, rules, permissions, escalations)
│   │       ├── mcp-server/    (Zoho MCP Node.js server)
│   │       ├── memory/        (agent memory)
│   │       ├── openclaw-config/ (separate OpenClaw instance config)
│   │       ├── prompts/       (system.md, Zoho MCP docs)
│   │       ├── skills/
│   │       │   ├── stt/      (STT module)
│   │       │   └── whatsapp/ (DoubleTick client/workflows)
│   │       ├── integrations/
│   │       │   └── doubletick.py
│   │       ├── zoho-config.json
│   │       ├── docker-compose.yml
│   │       └── Dockerfile
│   │
│   ├── leo/                    (68 MB) — LEO's own data
│   │   ├── agents/
│   │   ├── backups/
│   │   ├── browser-data/
│   │   ├── context/
│   │   ├── governance/
│   │   ├── hermes/            (HERMES prep — ⚠️ no active container)
│   │   ├── logs/
│   │   ├── memory/
│   │   ├── observability/
│   │   ├── services/
│   │   └── workflows/
│   │
│   ├── leo-data/               (16 KB)
│   │   ├── postgres/
│   │   └── redis/
│   │
│   ├── repos/
│   │   └── vss-infrastructure-docs/
│   │
│   ├── services/
│   │   └── stt/               (STT service source/config)
│   │
│   └── .openclaw/
│       ├── agents/
│       │   ├── main/          (LEO main agent)
│       │   │   ├── agent/
│       │   │   │   └── auth-profiles.json
│       │   │   └── sessions/
│       │   └── vsustain/      (⚠️ EMPTY — orphaned old workspace)
│       │
│       ├── workspace/          (LEO runtime workspace)
│       │   ├── VSS/           (legacy VSS materials — 112KB, pre-agent)
│       │   ├── agents/       (vsustain — empty)
│       │   ├── google-credentials/ (OAuth token + manager)
│       │   ├── skills/
│       │   ├── memory/
│       │   ├── docs/
│       │   └── *.md (identity/soul/agents/tools/user/memory files)
│       │
│       └── (runtime: openclaw.json, logs/, cron/, etc.)
│
└── /var/lib/docker/
    ├── volumes/
    │   ├── hermes-memory-data/  (⚠️ prepared for Hermes, no container)
    │   ├── leo-postgres data
    │   ├── leo-prometheus data
    │   └── leo-grafana data
    └── networks/
        └── hermes-network       (⚠️ prepared, no container yet)
```

---

## 12. ARCHITECTURE DIAGRAM

```
                                    ┌─────────────────────────────────────────┐
                                    │           AIforce (Azure VM Host)          │
                                    │  Ubuntu 24.04 · 2 vCPU · 8GB RAM · 61GB   │
                                    │                                             │
                                    │  ┌─────────────────────────────────────┐  │
                                    │  │  LEO 🦁 — Root AI (openclaw host)   │  │
                                    │  │  @Chotarajandonbot · MiniMax-M2.7   │  │
                                    │  │  Config: /home/aiops/.openclaw/     │  │
                                    │  └──────────────┬──────────────────────┘  │
                                    │                 │                           │
                                    │  ┌──────────────▼──────────────────────┐  │
                                    │  │  leo-observability network          │  │
                                    │  │                                      │  │
                                    │  │  leo-prometheus  :9090  (no targets)│  │
                                    │  │  leo-grafana     :3000              │  │
                                    │  │  leo-uptime      :3001 (healthy)    │  │
                                    │  └──────────────────────────────────────┘  │
                                    │                                             │
                                    │  ┌──────────────────────────────────────┐  │
                                    │  │  leo-browser        :9222           │  │
                                    │  │  ⚠️ Chrome debug port BROKEN         │  │
                                    │  └──────────────────────────────────────┘  │
                                    │                                             │
                                    │  ┌──────────────┐  ┌────────────────────┐   │
                                    │  │leo-postgres  │  │leo-redis           │   │
                                    │  │:5432 (loc)   │  │:6379               │   │
                                    │  │⚠️ unused     │  │⚠️ unused           │   │
                                    │  └──────────────┘  └────────────────────┘   │
                                    │                                             │
                                    │  ┌──────────────────────────────────────┐  │
                                    │  │  agent-network (172.23.0.0/16)       │  │
                                    │  │  ⚠️ EMPTY — no containers attached   │  │
                                    │  └──────────────────────────────────────┘  │
                                    └───────────────────┬───────────────────────┘
                                                         │ host.docker.internal
                    ┌────────────────────────────────────┴────────────────────────┐
                    │              stt_default (172.25.0.0/24)                    │
                    │                                                           │
                    │  ┌──────────────────────┐                                  │
                    │  │  stt-service :9001  │◄─────── STT requests            │
                    │  │  Python/FastAPI      │         (vss-agent)             │
                    │  │  [stt-stt-service]    │                                  │
                    │  └──────────────────────┘                                  │
                    └─────────────────────────────────────────────────────────────┘
                    ┌─────────────────────────────────────────────────────────────┐
                    │           vss_default (172.24.0.0/24)                       │
                    │                                                           │
                    │  ┌─────────────────────────────────────────────────────┐  │
                    │  │  vss-agent :18801→18789                             │  │
                    │  │  OpenClaw in Node:24 container                      │  │
                    │  │  Workspace: /home/aiops/agents/vss → /workspace     │  │
                    │  │                                                     │  │
                    │  │  VSustainAI ☀️                                     │  │
                    │  │  @VSustainAIbot                                    │  │
                    │  │                                                     │  │
                    │  │  ├── WhatsApp ──► DoubleTick API ──► Customers    │  │
                    │  │  ├── STT ─────────► host.docker.internal:9001      │  │
                    │  │  ├── Zoho MCP ────► ⚠️ signup pending              │  │
                    │  │  └── Governance rules (skills/whatsapp NOT message) │  │
                    │  └─────────────────────────────────────────────────────┘  │
                    └─────────────────────────────────────────────────────────────┘

        hermes-network ───────────────────────────────────────────────── ⚠️ PREPARED, NO CONTAINER YET
        hermes-memory-data volume ────────────────────────────────────── ⚠️ RESERVED, NOT IN USE
```

---

## 13. ISSUES & WEAKNESSES

### 🔴 Critical

| # | Issue | Detail |
|---|---|---|
| 1 | **Browser broken** | `leo-browser` Chrome debug port 9222 not responding — browser automation unusable |
| 2 | **PostgreSQL orphaned** | `leo-postgres` running but no active consumer — wasted container + storage |
| 3 | **Redis orphaned** | `leo-redis` running but no active consumer — wasted RAM + container |
| 4 | **HERMES infrastructure idle** | `hermes-network` + `hermes-memory-data` volume reserved but no container deployed |
| 5 | **Orphaned vsustain workspace** | `/home/aiops/.openclaw/agents/vsustain/` empty, confusing — old architecture remnant |
| 6 | **Disk 73% full** | 44 GB of 61 GB used — only ~18 GB free on system disk |

### 🟡 Medium

| # | Issue | Detail |
|---|---|---|
| 7 | **Zoho MCP incomplete** | Signup not done — MCP server exists but not connected |
| 8 | **Docker images 28.9 GB** | High image storage — 7.6 GB build cache with 2.1 GB reclaimable |
| 9 | **Google OAuth fragile** | OAuth "installed app" refresh tokens are one-time-use — need service account |
| 10 | **STT health endpoint broken** | `GET /health` returns 404 — uptime monitoring will fail |
| 11 | **Prometheus not scraping** | Prometheus running but no targets configured — not collecting any metrics |
| 12 | **Duplicate VSS directories** | `/home/aiops/.openclaw/workspace/VSS` (legacy) + `/home/aiops/agents/vss/` (active) |
| 13 | **Only 2 vCPUs** | Azure VM has 2 vCPUs — fine for current load but limiting for multi-agent |
| 14 | **Swap at 45%** | 1.8 GB of 4 GB swap used — may indicate memory pressure |
| 15 | **DoubleTick key in source files** | API key hardcoded in `doubletick.py` — should be in env vars or secrets manager |

### 🟢 Observations

| # | Note |
|---|---|
| 16 | STT service is actively used — vss-agent continuously transcribing |
| 17 | vss-agent governance rules are well-structured and enforced |
| 18 | leo-uptime shows healthy status — monitoring itself works |
| 19 | Docker build cache reclaimable — 2.1 GB can be recovered |

---

## 14. RECOMMENDATIONS BEFORE HERMES DEPLOYMENT

### Immediate (Do First)
1. **Clean orphaned resources** — remove vsustain empty workspace, decide if legacy VSS dir is needed
2. **Fix or remove leo-browser** — repair Chrome debug OR `docker stop leo-browser` to free resources
3. **Decide on PostgreSQL/Redis** — either wire into vss-agent or remove (`docker stop leo-postgres leo-redis && docker rm`)
4. **Docker cleanup** — `docker system prune -a` to reclaim 2.1 GB+ of build cache

### High Priority
5. **Disk space** — at 73% with only 18 GB free, need cleanup before deploying new agents
   - `docker system df` to identify biggest consumers
   - Remove old images, prune volumes
   - Clear `/home/aiops/leo/` old logs and backups
6. **Fix STT health endpoint** — update `/health` route to return 200 so monitoring works
7. **Configure Prometheus targets** — add scrape configs for containers that need monitoring
8. **Complete Zoho MCP signup** — https://www.zoho.com/mcp/signup.html to enable Zoho CRM

### Before Hermes
9. **HERMES decision** — `hermes-network` and `hermes-memory-data` are prepped but unused
   - Either deploy HERMES agent or clean up the prep to avoid confusion
10. **Google OAuth service account** — set up service account for permanent Sheets access (current refresh tokens are fragile)

---

## 15. SERVICE DEPENDENCY MAP

```
Abhishek (Telegram)
        │
        ▼
┌───────────────────┐
│ @Chotarajandonbot │ (LEO host)
│  MiniMax-M2.7     │
└─────────┬─────────┘
          │
          │ (escalation only)
          ▼
┌─────────────────────────┐
│ @VSustainAIbot          │ (vss-agent container)
│  WhatsApp ──► DoubleTick│
│  STT ───────► host:9001 │
│  Zoho ──────► (pending) │
└────────────┬────────────┘

Monitoring (separate):
  Prometheus ──► (no targets configured)
  Grafana ◄──── Prometheus
  Uptime Kuma ──► (self-monitoring healthy)

Storage:
  hermes-memory-data ──► (unused volume)

Network isolation:
  stt_default ────► stt-service ↔ vss-agent
  vss_default ────► vss-agent only
  leo-observability ──► prometheus/grafana/uptime
  agent-network ────► (empty)
  hermes-network ────► (empty)
```

---

**Report generated by LEO 🦁**
**Audit date:** 2026-06-01
**Sources:** Docker inspect, filesystem scan, service health checks, network inspection, config files, container logs.
