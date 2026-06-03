# MEMORY.md — LEO Long-Term Memory

**Last updated:** 2026-05-31  
**Last audit:** Complete resource self-audit done 2026-05-31

---

## Who I Am

**Name:** LEO (Legal Entity Orchestrator, or just "Leo")  
**Emoji:** 🦁  
**Identity:** Root AI Orchestrator  
**Platform:** `@Chotarajandonbot` on Telegram (`[REDACTED]`)  
**Host:** AIforce — bare metal, Ubuntu 24.04, Linux 6.17.0-1013-azure, user: `aiops`  
**Runtime:** OpenClaw running as host process (`openclaw`)  
**Workspace:** `/home/aiops/.openclaw/workspace/`  
**Config:** `/home/aiops/.openclaw/openclaw.json`

---

## Who I Work For

**Abhishek Sharma** (@abhishekmightcode, @Chot_Abhishek on Telegram, ID: 1107443153)
- Runs multiple ventures — VSS, PanaceaX, Solar-Bangalore, Agency work
- Prefers Telegram + voice notes for communication
- GitHub: https://github.com/abhishekmightcode/Projects-with-leo

---

## Docker Containers on AIforce

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| **vss-agent** | `openclaw:local` | 18801 → 18789 | **VSustainAI agent (ISOLATED)** |
| **stt-service** | `stt-stt-service` | 9001 | **Speech-to-text service** |
| leo-browser | `ghcr.io/browserless/chromium` | 9222 | Browser automation (BROKEN — debug port not responding) |
| leo-uptime | `louislam/uptime-kuma` | 3001 | Monitoring |
| leo-grafana | `grafana/grafana` | 3000 | Metrics dashboards |
| leo-prometheus | `prom/prometheus` | 9090 | Metrics collection |
| leo-postgres | `postgres:16` | 5432 (local only) | Database |
| leo-redis | `redis:7` | 6379 | Cache/queue |

All on Docker network `agent-network`.

---

## VSustainAI Agent (vss-agent)

**Container:** `vss-agent` (openclaw:local)
- **Workspace:** `/home/aiops/agents/vss/` (bind-mounted to container `/workspace`)
- **Config inside container:** `/root/.openclaw/openclaw.json` (separate from host LEO config)
- **Identity:** `VSustainAI` ☀️ — autonomous solar operations and CRM agent
- **Telegram bot:** token `[REDACTED_BOT_TOKEN]` (bot: `@VSustainAIbot`)
- **Governance files:** `/workspace/governance/` — identity.md, rules.md, permissions.md, escalations.md
- **Memory:** `/workspace/memory/identity.md`
- **Docker network IP:** `172.23.0.2`
- **Uptime:** Container started ~May 27

**Zoho MCP Integration (in progress):**
- Config: `/agents/vss/zoho-config.json`
- MCP server: `/agents/vss/mcp-server/` (Node.js)
- Credentials: clientId `[REDACTED]`
- Knowledge base: `/agents/vss/prompts/ZOHO_MCP_KNOWLEDGE_BASE.md`
- Learning prompt: `/agents/vss/prompts/ZOHO_MCP_LEARN.md`
- **Status:** Awaiting Abhishek to complete Zoho MCP signup at https://www.zoho.com/mcp/signup.html

---

## LEO (host process) vs VSustainAI (container)

| | LEO (me) | VSustainAI |
|-|----------|------------|
| **Runtime** | Host process `openclaw` (bare metal) | Docker container `vss-agent` |
| **Config** | `/home/aiops/.openclaw/openclaw.json` | `/root/.openclaw/openclaw.json` (container) |
| **Workspace** | `/home/aiops/.openclaw/workspace/` | `/home/aiops/agents/vss/` |
| **Telegram** | `@Chotarajandonbot` | `@VSustainAIbot` |
| **Identity** | LEO 🦁 ROOTAI | VSustainAI ☀️ |

---

## 🔑 PERMANENT SECRETS & CREDENTIALS

### GitHub
- **PAT stored in:** `~/.git-credentials` (git credential helper)
- **Repo:** https://github.com/abhishekmightcode/Projects-with-leo

### Google Sheets (WORKING — needs service account fix)
- **OAuth Client ID:** `[REDACTED - see google-credentials/token.json]`
- **OAuth Client Secret:** `[REDACTED - see google-credentials/token.json]`
- **Refresh Token:** `[REDACTED - see google-credentials/token.json]`
- **Token Manager Script:** `/workspace/google-credentials/token_manager.py`
- **Account:** `vsustainsolarenergy@gmail.com`
- **Sheet (old - engineering colleges):** `1HWmgUfy4Wr6hz2FVLLPf2OmLx352fYghVFNUjBMKcUM`
- **Sheet (new - ITI & Diploma):** `1_gTviQ9FFUXF4-K_aDcHxsh2zhqo7PkGEtp9OuiK5IQ`
- **⚠️ KNOWN ISSUE:** OAuth "installed app" refresh tokens are one-time use — need service account for permanent access
- **⚠️ KNOWN ISSUE:** Token manager script is broken — access token shows as "expired" (expired_at in past)

### Telegram Bots
- **LEO bot:** `[REDACTED]` → `@Chotarajandonbot`
- **VSustainAI bot:** `[REDACTED_BOT_TOKEN]` → `@VSustainAIbot`

### DoubleTick (WhatsApp for VSS)
- **API Key:** `key_Ru…7ssn` (in `doubletick.py`)
- **WABA Number:** `919900108067`
- **Location:** `/workspace/VSS/integrations/doubletick.py`

### Zoho
- **Client ID (old):** `[REDACTED]`
- **Client Secret (old):** `[REDACTED]`
- **Refresh Token (old):** `[REDACTED]`
- **Client ID (new):** `[REDACTED]`
- **Client Secret (new):** `[REDACTED]`
- **Refresh Token (new):** `1000.6…8b2a`
- **API Domain:** `https://www.zohoapis.in`
- **Scope:** `ZohoCRM.modules.ALL`
- **Location:** `/agents/vss/zoho-config.json`, `/agents/vss/mcp-server/.env`

---

## 📊 PROJECT DATA

### Bangalore Engineering Colleges T&P Database (May 2026)
- **Sheet:** https://docs.google.com/spreadsheets/d/1HWmgUfy4Wr6hz2FVLLPf2OmLx352fYghVFNUjBMKcUM
- **Rows:** 137 data rows, 113 unique colleges
- **Phone:** 91%, Email: 84%, Director: 96%
- **Status:** Complete, not actively maintained

### Bangalore ITI & Diploma Colleges T&P Database (May 2026)
- **Sheet:** https://docs.google.com/spreadsheets/d/1_gTviQ9FFUXF4-K_aDcHxsh2zhqo7PkGEtp9OuiK5IQ
- **Rows:** 44 colleges (30 polytechnic + 14 ITI)
- **Enrichment:** Partial — most govt institutes have no online presence
- **Files:** `/workspace/bangalore_polytechnic_colleges.json`, `/workspace/bangalore_iti_colleges.json`
- **Status:** Complete baseline, needs manual enrichment

---

## 🛠️ SKILLS AVAILABLE

All skills are at `/usr/lib/node_modules/openclaw/skills/`:

**Productivity:** notion, taskflow, taskflow-inbox-triage, weather, summarize  
**Communication:** telegram (native), whatsapp (wacli), slack, discord  
**Development:** github, coding-agent, node-inspect-debugger, python-debugpy  
**Data:** spreadsheet (native Google Sheets API), pdf, video-frames  
**Media:** image_generate, image, music_generate, video_generate, tts  
**Utilities:** tmux, session-logs, healthcheck, spike, skill-creator, canvas  
**AI/ML:** openai-whisper, openai-whisper-api, gemini  
**Special:** gh-issues, diagram-maker, meme-maker, blogwatcher

**NOT installed/working:**
- `openai-whisper` skill available but not configured
- `leo-browser` container running but Chrome debug port not responding

---

## ⚠️ KNOWN ISSUES & FIXES NEEDED

| Issue | Status | Fix |
|-------|--------|-----|
| Google OAuth refresh fails | Known | Switch to service account (Abhishek to set up) |
| Web search (Kimi) | Broken | Use MiniMax native web search via subagents |
| leo-browser debug port | Not responding | Restart `leo-browser` container |
| VSS MCP token rate limited | Zoho throttling | Wait and retry, credentials may be old |
| STT service | Discovered but purpose unclear | Investigate what it's for |

---

## What I Learned (Self-Awareness)

- The `vsustain` workspace at `/home/aiops/.openclaw/agents/vsustain/` is **EMPTY/ORPHANED** — remnant from old plan, NOT the active agent
- The active VSS agent is `vss-agent` Docker container with workspace at `/home/aiops/agents/vss/`
- Both LEO and VSustainAI run MiniMax-M2.7 via minimax-portal
- LEO's auth profiles: `/home/aiops/.openclaw/agents/main/agent/auth-profiles.json`
- STT service exists on port 9001 — purpose needs investigation

---

*LEO 🦁 — last updated 2026-05-31 after full self-audit*