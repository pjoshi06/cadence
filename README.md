# Cadence — AMS Operations Hub (MVP)

Internal portal for an AMS team: task board, leave management, ticket data and
automated DSR / WSR / MSR PowerPoint generation.

**Stack:** Django 6 · HTMX · Tailwind (CDN) · SQLite · python-pptx

## Run it

```powershell
venv\Scripts\python.exe manage.py runserver
```

Open http://localhost:8000 — demo login: `puneet` / `demo1234`
(other seeded users: anita, rahul, priya, vikram, sneha — same password).

First-time setup on a new machine:

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py seed_demo   # optional demo data
```

## Modules

| Area | What it does |
|---|---|
| Dashboard | Open tickets by priority, SLA %, resolved this week, who's on leave, team workload bars, my tasks, recent reports |
| Tasks | Team task board with filters and inline (HTMX) status updates; tracks ticket + non-ticket work |
| Tickets | CSV import standing in for the ServiceNow feed (`Sample CSV` shows the expected columns); re-import upserts by ticket number |
| Leaves | Apply / approve / reject (HTMX), month calendar of team availability |
| Shift Roster | Weekly members × days grid with colour-coded shifts, inline HTMX editing for managers, ⚠ flags on approved-leave days, per-day coverage counts, copy-last-week, week navigation |
| Shift Master | Manager-only screen (Admin → Shift Master) to create/edit shifts — code, name, timings, colour, active flag. Shifts used on rosters are deactivated instead of deleted so history is preserved; only active shifts are offered when assigning |
| Change Reviews | Tracks engineering changes through AMS review: runbook handover, walkthrough scheduling, first/second reviews, approval — each step timestamped with who did it. Runbook file upload, reviewer assignment, turnaround metrics (runbook → first review, total cycle), and a "Change Management" slide in report decks |
| Batch Health | Control-M job monitoring: Job Master (name, category, criticality, schedule, cluster) + 7-day status grid with inline HTMX updates, failures-today banner with remarks/INC refs, "mark rest success" for the morning check, runs CSV import (auto-creates unknown jobs), dashboard tile, and an automatic "Batch Job Status" slide in DSR/WSR/MSR decks |
| Reports | Generate DSR/WSR/MSR `.pptx` from ticket data + manager highlights; report history with downloads |
| PPT Templates | Upload client-approved `.pptx` templates (branding is kept, report slides are appended); a built-in neutral default template always available |
| Team | Onboard members with portal role, ServiceNow user/group mapping, skills, leave balance; deactivate on offboarding |

## Report generation

`reports/pptgen.py` builds 5 slides: Title, Executive Summary (KPIs + priority
mix), Backlog Ageing & P1/P2 focus list, Resolved in Period, Highlights &
Manager Notes. With an uploaded client template the client's slide master is
reused; otherwise the built-in styled default is used.

## Next steps (beyond MVP)

- ServiceNow REST Table API connector to replace the CSV import (needs a
  service account — request read access to your assignment groups)
- SSO (Azure AD via `mozilla-django-oidc` or `django-allauth`) replacing local passwords
- Scheduled nightly sync + auto-draft DSR (Celery/APScheduler)
- PostgreSQL + proper `SECRET_KEY`/`DEBUG=False` before any shared deployment
