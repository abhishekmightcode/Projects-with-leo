# 🤖 AIforce Infrastructure Audit Report

**Generated:** 2026-06-02 17:57 UTC
**Host:** AIforce
**Auditor:** LEO 🦁

---

## 1. SERVER OVERVIEW

| Property | Value |
|---|---|
| **Hostname** | `AIforce` |
| **OS** | Ubuntu 24.04 LTS |
| **Kernel** | Linux 6.17.0-1013-azure |
| **CPU** | AMD EPYC 7763 64-Core (2 vCPUs allocated) |
| **RAM** | 7.8 GB total · ~4 GB used · ~3.8 GB available |
| **Swap** | 4 GB total · ~1.8 GB used |
| **Disk** | 61 GB total · **42 GB used (69%)** · **20 GB free** |
| **Architecture** | x86_64 Azure VM |
| **Container Runtime** | Docker |

### 📊 Storage Action Taken
- Ran `docker system prune --filter "until=168h"` — freed **2.1 GB** from build cache
- Disk went from 73% → 69% (44G → 42G used)

---

## 2. CONTAINER INVENTORY

| CONTAINER | IMAGE | STATUS | SIZE | PORTS | PURPOSE |
|---|---|---|---|---|---|
| `vss-agent` | `vss-vss-agent` (local) | Up 7d | **11.4 GB** | 18801→18789/tcp | VSustainAI agent (ISOLATED) ☀️ |
| `stt-service` | `stt-stt-service` (local) | Up 6d | 487 MB | 9001/tcp | Speech-to-text service |
| `leo-browser` | `ghcr.io/browserless/chromium` | Up 8d | 770 KB | 9222/tcp | Browser automation ⚠️ **BROKEN** |
| `leo-uptime` | `louislam/uptime-kuma` | Up 8d | 262 KB | 3001/tcp | Uptime monitoring |
| `leo-grafana` | `grafana/grafana` | Up 9d | 54.8 MB | 3000/tcp | Metrics dashboards |
| `leo-prometheus` | `prom/prometheus` | Up 9d | 4.1 KB | 9090/tcp | Metrics collection |
| `leo-postgres` | `postgres:16` | Up 9d | 28.7 KB | 5432/tcp (localhost) | Database ⚠️ no active consumer |
| `leo-redis` | `redis:7` | Up 9d | 4.1 KB | 6379/tcp | Cache/queue ⚠️ no active consumer |

### ⚠️ Warnings
- **`vss-agent` is HUGE** — 11.4 GB writable layer, 14.1 GB virtual. Likely contains large Python/Conda environments, node_modules, or cached models
- **`leo-browser`** — Chrome debug port not responding; container is effectively dead
- **`leo-postgres` & `leo-redis`** — No active consumers; running idle

---

## 3. DOCKER DISK USAGE

```
TYPE            TOTAL  SIZE      RECLAIMABLE
Images          8      27.44 GB  0B
Containers      8      11.91 GB  0B
Local Volumes   4      116.3 MB   176 B
Build Cache     22     5.45 GB    36.86 KB
```

### Largest Images
| Image | Size |
|---|---|
| `vss-vss-agent` (local) | ~14 GB virtual |
| `ghcr.io/browserless/chromium` | 2.87 GB |
| `stt-stt-service` | 1.79 GB |
| `louislam/uptime-kuma` | 568 MB |
| `grafana/grafana` | 1.16 GB |

---

## 4. FILESYSTEM & DISK CONSUMPTION

### Key Directories
| Path | Size | Notes |
|---|---|---|
| `/home/aiops/agents` | 260 MB | Active agent workspaces |
| `/home/aiops/leo` | 68 MB | LEO runtime files |
| `/home/aiops/repos` | 208 KB | Git repos |
| `/home/aiops/.cache` | — | pip, uv, whisper models |
| `/.local/lib/python3.12` | — | pip packages (numpy, scipy, torch, triton) |

### Large Files Found
| File | Size |
|---|---|
| `uv` binary | >10 MB |
| `libscipy_openblas64` | >100 MB |
| `libllvmlite.so` | >100 MB |
| Triton NVIDIA backends (ptxas, cupti) | ~100 MB each |
| Torch library files | ~500 MB each |
| Whisper models (`large-v3-turbo.pt`, `small.pt`) | ~3 GB combined |

---

## 5. ORPHANED / UNUSED ASSETS

### Old Workspace (EMPTY)
- `/home/aiops/.openclaw/agents/vsustain/` — **12 KB only** — remnant from old architecture, no content

### Node Modules (Package Bloat)
- `vss-agent` openclaw-config has extensive `node_modules/` in `extensions/whatsapp/` — images, test snapshots, fonts (~50 MB of icons/test images alone)
- Various Python package test assets (sympy, networkx matplotlib tests)

### Unused Containers
- `leo-postgres` — running but no consumer
- `leo-redis` — running but no consumer
- `leo-browser` — broken (Chrome debug port unresponsive)

---

## 6. KNOWN ISSUES

| # | Issue | Status | Fix |
|---|---|---|---|
| 1 | Google OAuth refresh tokens expire | **KNOWN** | Need service account switch |
| 2 | Web search (Kimi) broken | **KNOWN** | Use MiniMax native search via subagents |
| 3 | `leo-browser` debug port unresponsive | **BROKEN** | Restart container (`docker restart leo-browser`) |
| 4 | VSS MCP token rate limited | **Zoho throttling** | Wait and retry |
| 5 | `vss-agent` container is **11.4 GB** | **BLOAT** | Needs slim-down: remove node_modules/test assets/Conda envs |
| 6 | `leo-postgres` & `leo-redis` idle | **WASTE** | Consider stopping if not needed |
| 7 | STT service discovered but purpose unclear | **INVESTIGATE** | Document what it's for |

---

## 7. RECOMMENDATIONS (Priority Order)

### 🔴 HIGH PRIORITY
1. ** Slim down `vss-agent` container** — 11.4 GB is excessive
   - Remove unused `node_modules` / test assets / __pycache__
   - Clean Conda/pip cache inside container
   - Consider rebuilding image from scratch with slim base

### 🟡 MEDIUM PRIORITY
2. **Fix `leo-browser`** — restart container to restore Chrome debug port
3. **Investigate `leo-postgres`/`leo-redis`** — either connect consumers or stop them
4. **Document STT service purpose** — what is it actually used for?

### 🟢 LOW PRIORITY
5. **Clean up orphaned workspace** (`/home/aiops/.openclaw/agents/vsustain/`)
6. **Switch to service account for Google Sheets** — fix OAuth refresh issue permanently

---

## 8. GIT REPO STATUS

**Repo:** `https://github.com/abhishekmightcode/Projects-with-leo`
**Branch:** `master`

### Recent Commits
| Commit | Message |
|---|---|
| `093142d` | Add infrastructure audit report — 2026-06-01 |
| `e124b06` | VSustainAI governance: WhatsApp rules |
| `23a1fd5` | LEO: Add modular WhatsApp framework for VSustainAI |
| `52497e0` | LEO: Document STT fix process for VSustainAI |
| `2d1927d` | LEO: Add VSustainAI STT skills |
| `93c2000` | LEO: Add centralized STT skills for ROOTAI |
| `971630d` | LEO: Add STT Ecosystem docs |
| `a3d6d54` | LEO: Add VSS DoubleTick integration |

### Untracked Files (not committed)
- Workspace config files (`AGENTS.md`, `SOUL.md`, `MEMORY.md`, `TOOLS.md`, etc.)
- `VSS/` directory (integrations, knowledge base)
- `google-credentials/`
- `bangalore_colleges_data.md`, `bangalore_iti_colleges.json`, etc.
- `vsustain/` (orphaned workspace)

---

**Next Audit Scheduled:** 2026-06-09 (weekly)

*LEO 🦁 — AIforce Infrastructure Auditor*