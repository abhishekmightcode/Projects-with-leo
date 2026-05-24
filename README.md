# Projects with LEO

> **Purpose:** Complete project visibility and management for Abhishek Sharma's ventures — startup, agency, and all client work. If LEO loses context, this repo must have everything needed to understand any project, any plan, any status.

**Managed by:** LEO (Root Infrastructure Orchestrator)  
**Owner:** Abhishek Sharma (@abhishekmightcode)  
**GitHub:** https://github.com/abhishekmightcode/Projects-with-leo

---

## 🏗️ Repository Structure

```
Projects-with-leo/
│
├── README.md                         ← You are here
│
├── COHORTS/                          ← Top-level folders by cohort/venture
│   │
│   ├── VSS/                          ← V Sustain Solar Solutions
│   │   ├── README.md                 ← Project overview & status
│   │   ├── PLANS/                    ← All project plans
│   │   ├── IMPLEMENTATIONS/          ← What was built
│   │   ├── STATUS.md                 ← Current status
│   │   ├── CREDENTIALS.md            ← Credential reference (no secrets)
│   │   └── docs/
│   │
│   ├── PanaceaX/                     ← AI-native CRM venture
│   │   ├── README.md
│   │   ├── PLANS/
│   │   ├── RESEARCH/
│   │   └── docs/
│   │
│   ├── Solar-Bangalore/               ← Solar market research
│   │   └── README.md
│   │
│   └── Agency-Clients/               ← Agency client work
│       ├── README.md
│       └── [client-folders/]
│
└── .leo/                             ← LEO's operational notes
    └── LEO-INSTRUCTIONS.md           ← How LEO manages this repo
```

---

## 🚦 Project Status At a Glance

| Project | Cohort | Status | Priority |
|---------|--------|--------|----------|
| **VSS** | VSS | 🔴 ACTIVE | HIGH |
| **PanaceaX** | PanaceaX | 🟡 EXPLORATION | MEDIUM |
| **Solar-Bangalore** | Solar-Bangalore | ⚪ PAUSED | LOW |
| **Agency Clients** | Agency-Clients | 🔵 TBD | — |

---

## 📌 How LEO Manages This Repo

### Project Assignment Protocol

When Abhishek assigns a new project:

1. **Identify the cohort** → determine which COHORT folder it belongs to
2. **Create project folder** → `COHORTS/<cohort>/<project-name>/`
3. **Create standard structure** → README, PLANS, IMPLEMENTATIONS, docs
4. **Create initial PLAN** → document the project, goals, approach, and first steps
5. **Push to GitHub** → `gh repo push` immediately so Abhishek can read along
6. **Track in context** → write project name + folder path to `/home/aiops/leo/context/active-project.md`

### LEO's Rules for This Repo

1. **Every new project** → create folder in the correct COHORT before doing anything else
2. **Every plan** → write as `.md` in `PLANS/` under that project
3. **Every implementation** → document in `IMPLEMENTATIONS/` under that project
4. **Never push secrets** → CREDENTIALS.md contains reference paths only
5. **Context continuity** → if session resets, read `active-project.md` from `/home/aiops/leo/context/`
6. **Abhishek can read all** → all docs written in clear English, structured for human readability

---

## 🔑 Current Active Projects

### VSS (V Sustain Solar Solutions)
- **Cohort:** VSS
- **Status:** 🔴 ACTIVE
- **What:** Field app for solar company dealers — GPS, photo upload, Zoho CRM sync
- **Repo:** https://github.com/abhishekmightcode/vss-ups-field-app
- **Live:** https://abhishekmightcode.github.io/vss-ups-field-app/
- **Docs:** See `COHORTS/VSS/`

### PanaceaX
- **Cohort:** PanaceaX
- **Status:** 🟡 EXPLORATION
- **What:** AI-native CRM build using Zoho as platform
- **Docs:** See `COHORTS/PanaceaX/`

---

*Last updated by LEO: 2026-05-24*