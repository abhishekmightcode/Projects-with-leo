# TOOLS.md - LEO Quick Reference

## 🚨 Critical Credentials (permanent)

### Google Sheets
- **Token refresh:** Use `python3 /home/aiops/.openclaw/workspace/google-credentials/token_manager.py`
- **Auth code flow:** Get code from `http://localhost:3000/api/auth/google/callback?code=...`
- **Sheet IDs:**
  - Engineering colleges: `1HWmgUfy4Wr6hz2FVLLPf2OmLx352fYghVFNUjBMKcUM`
  - ITI & Diploma: `1_gTviQ9FFUXF4-K_aDcHxsh2zhqo7PkGEtp9OuiK5IQ`
- **⚠️ Note:** OAuth tokens need service account for permanent access (in progress with Abhishek)

### GitHub
- PAT stored in `~/.git-credentials` (git credential helper handles it)
- No need to manually handle — git commands work automatically
- Repo: https://github.com/abhishekmightcode/Projects-with-leo

### Telegram Bots
- LEO: `@Chotarajandonbot` (token in openclaw.json)
- VSustainAI: `@VSustainAIbot` (token in container config)

### DoubleTick (WhatsApp)
- Code at: `/home/aiops/.openclaw/workspace/VSS/integrations/doubletick.py`
- API Key, WABA number all in that file

### Zoho
- Config: `/home/aiops/agents/vss/zoho-config.json`
- MCP .env: `/home/aiops/agents/vss/mcp-server/.env`
- **Signup needed:** https://www.zoho.com/mcp/signup.html

---

## 🔧 Common Operations

### Write to Google Sheet
```bash
curl -s -X POST "https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/A1:append?valueInputOption=RAW" \
  -H "Authorization: Bearer $(python3 /home/aiops/.openclaw/workspace/google-credentials/token_manager.py)" \
  -H "Content-Type: application/json" \
  -d '{"values": [[...rows...]]}'
```

### Check Docker containers
```bash
docker ps --format "{{.Names}}\t{{.Status}}"
```

### Restart leo-browser (if Chrome debug port unresponsive)
```bash
docker restart leo-browser
```

### Check STT service
```bash
curl -s http://localhost:9001/health
```

### Git operations (automatic with credential helper)
```bash
cd /home/aiops/.openclaw/workspace
git pull / git push  # works automatically via git-credentials
```

---

## 📁 Key File Locations

| File | Path |
|------|------|
| LEO MEMORY.md | `/home/aiops/.openclaw/workspace/MEMORY.md` |
| Google credentials | `/home/aiops/.openclaw/workspace/google-credentials/token.json` |
| Token manager | `/home/aiops/.openclaw/workspace/google-credentials/token_manager.py` |
| VSS Agent workspace | `/home/aiops/agents/vss/` |
| DoubleTick code | `/home/aiops/.openclaw/workspace/VSS/integrations/doubletick.py` |
| Zoho config | `/home/aiops/agents/vss/zoho-config.json` |
| Bangalore polytechnic data | `/home/aiops/.openclaw/workspace/bangalore_polytechnic_colleges.json` |
| Bangalore ITI data | `/home/aiops/.openclaw/workspace/bangalore_iti_colleges.json` |
| OpenClaw config (host) | `/home/aiops/.openclaw/openclaw.json` |

---

## 🌐 Web Search & Browser

### Web Search
- **Primary:** MiniMax native search via subagents (model: minimax-portal/MiniMax-M2.7)
- **Kimi (web_search tool):** Broken — API key not configured
- **Workaround:** Spawn subagent with `model=minimax-portal/MiniMax-M2.7` and instruct it to use web_search

### Browser (leo-browser)
- Container: `leo-browser` on Docker network `agent-network`
- Chrome debug port: 9222
- **If not responding:** Restart container with `docker restart leo-browser`

---

## 🧠 Skills Reference

Quick lookup — full list at `/usr/lib/node_modules/openclaw/skills/`

| Need | Skill |
|------|-------|
| GitHub PRs/issues | `github` |
| Notion pages | `notion` |
| Weather | `weather` |
| Tmux control | `tmux` |
| Python debugging | `python-debugpy` |
| Node.js debugging | `node-inspect-debugger` |
| Health check | `healthcheck` |
| Create diagrams | `diagram-maker` |
| Video frames | `video-frames` |
| Task automation | `taskflow` |
| Canvas ( Presentations) | `canvas` |

---

## 📝 Daily Memory

Create files at `/home/aiops/.openclaw/workspace/memory/YYYY-MM-DD.md` for session continuity.
- Already exists: `2026-05-26.md`, `2026-05-27.md`

---

*Updated: 2026-05-31 after full self-audit*