# VSS — V Sustain Solar Solutions

## Overview

**What:** Field app for VSS (V Sustain Solar Solutions) — a Bangalore-based solar company.
**Purpose:** Field employees manage dealer relationships, submit location, info, and photos to Zoho CRM.
**Live:** https://abhishekmightcode.github.io/vss-ups-field-app/

---

## Tech Stack

- **Frontend:** Firebase-backed web app (static hosting on GitHub Pages)
- **Backend:** Zoho CRM (source of truth)
- **Sync:** Zoho → Firebase cron job (hourly sync, job ID `e7474b1dd47e`)
- **Deployment:** GitHub Pages (public)

---

## Data Model

- **Firebase doc ID** = Zoho record ID (e.g. `1171062000002901006`)
- **`dealer_code`** = secondary key stored as field inside each doc (e.g. `1000036809`)
- **Zoho DC:** `.in` (India) — `crm.zoho.in`, token URL `https://accounts.zoho.in/oauth/v2/token`

---

## Features

1. **View Dealer List** — instant load from Firebase cache
2. **Send Location** — GPS → Zoho CRM via `PUT /crm/v2/UPS/{record_id}`
3. **Submit Info** — in-app form → Zoho CRM via `PUT` + creates Dealer Meets entry via `POST`
4. **Upload Photo** — Google Form (photo only, for now)
5. **Hourly Sync** — Zoho → Firebase (cron job)

---

## Key Rules

- Zoho is source of truth
- Firebase is read-cache (can be rebuilt from Zoho)
- All text entry via in-app web form → direct Zoho API
- No Google Forms for text entry
- Firebase doc ID = Zoho record ID = PRIMARY KEY

---

## Status

- 🔴 ACTIVE — Field app is live and in use
- See `STATUS.md` for current issues and next steps
- See `PLANS/` for roadmap

---

*Last updated by LEO: 2026-05-24*