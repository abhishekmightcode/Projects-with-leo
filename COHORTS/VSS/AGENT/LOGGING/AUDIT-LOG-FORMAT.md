# VSS Agent — Audit Log Format

**Agent:** vsustain-agent (Pravesh's AI Assistant)  
**Supervisor:** LEO  
**Purpose:** Every action logged, reviewable, traceable

---

## Log Directory Structure

```
/home/aiops/leo/agents/vsustain/workspace/logs/
├── actions/
│   ├── 2026-05-24.md
│   ├── 2026-05-25.md
│   └── anomalies.md
├── conversations/
│   ├── 2026-05-24.md
│   └── 2026-05-25.md
└── reviews/
    └── LEO-review.md
```

---

## Action Log Format

Each action in `logs/actions/YYYY-MM-DD.md`:

```markdown
## [HH:MM:SS] Action: <action_type>

**Trigger:** Pravesh's command (verbatim or paraphrase)
**Customer:** <name or "general">
**Details:**
  - <detail 1>
  - <detail 2>

**Result:** <success/failed/pending>
**Status:** <routine/flagged/escalated>
**LEO Review:** <yes/no/pending>
**Timestamp:** YYYY-MM-DD HH:MM:SS UTC
```

---

## Action Types

| Action | Description |
|--------|-------------|
| `send_whatsapp` | Sent WhatsApp message to customer |
| `zoho_update` | Updated CRM record |
| `contact_search` | Searched Google Contacts |
| `price_quote` | Generated price quotation |
| `task_created` | Created scheduled task |
| `task_completed` | Task executed |
| `web_search` | Did market research |
| `anomaly_detected` | Flagged unusual behavior |
| `leO_escalation` | Requested LEO approval |
| `leO_approved` | LEO approved action |
| `leO_denied` | LEO denied action |

---

## Conversation Log Format

```markdown
# 2026-05-24 Conversation Log

## Session 1 — 09:00 to 09:45 IST

**Pravesh:** [message or voice summary]
**Agent:** [response]
**Action taken:** [none/send_whatsapp/zoho_update/etc]
**Learning:** [new info captured for adaptation]

---

## Session 2 — 14:30 IST

**Pravesh:** [message or voice summary]
**Agent:** [response]
**Action taken:** [send_whatsapp to Rajesh]
**Learning:** [Rajesh prefers 5kVA over 3kVA]
```

---

## Anomaly Log Format

```markdown
# Anomalies Log

## [YYYY-MM-DD HH:MM] — SEVERITY: <low/medium/high/critical>

**What happened:** <description>
**Triggered by:** <Pravesh command or internal>
**Agent response:** <what agent did>
**LEO notified:** <yes/no>
**Resolution:** <approved/denied/blocked>
**Notes:** <anything relevant>

---
```

---

## LEO Review Format

LEO reviews logs daily (or on-demand). Notes in `reviews/LEO-review.md`:

```markdown
# LEO Review — 2026-05-24

## Actions Reviewed
- Total: 47
- Routine: 45
- Flagged: 2
- Escalated: 0

## Notable Events
- [event 1]
- [event 2]

## Anomalies
- [anomaly 1 - resolved]
- [anomaly 2 - monitoring]

## Recommendations
- [recommendation 1]
- [recommendation 2]

## Agent Performance
- Learning quality: good/needs improvement
- Accuracy: X%
- Pending concerns: [list]

---
```

---

## Retention Policy

| Log Type | Keep For |
|----------|----------|
| Action logs | 90 days |
| Conversation logs | 90 days |
| Anomaly logs | 1 year |
| LEO reviews | 1 year |
| Customer profiles | Until Pravesh deletes |

---

## How LEO Reviews

1. LEO reads `logs/actions/YYYY-MM-DD.md` each morning
2. Flags anomalies to `logs/anomalies.md`
3. If severe → LEO messages Abhishek on Telegram
4. If routine → LEO notes in `reviews/LEO-review.md` and moves on

---

*Audit Log v2 — LEO — 2026-05-24*