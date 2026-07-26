# Taking Cadence to production (~60 users)

60 users is a light load (expect 10–15 concurrent at peak). One modest server
handles it comfortably — the work is in hardening, not scaling.

## 1. Infrastructure

- **One VM on company infrastructure**: 2 vCPU, 4 GB RAM, 40 GB disk.
  Ubuntu LTS + nginx + gunicorn is the well-trodden path. (Windows Server +
  IIS/HttpPlatformHandler works if that's what your org supports.)
- **Keep it inside the corporate network / VPN.** Client ticket data should
  never sit on the public internet.
- Docker is optional at this scale — a systemd service is simpler to operate.

## 2. Code changes before deploy (in this repo)

| Item | Today (MVP) | Production |
|---|---|---|
| `SECRET_KEY` | hardcoded in settings.py | from env var, newly generated |
| `DEBUG` | `True` | `False`, set `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` |
| Database | SQLite | PostgreSQL 16 (`dumpdata`/`loaddata` to migrate) |
| Tailwind | CDN script | compiled CSS via Tailwind standalone CLI, self-hosted |
| HTMX / Inter font | CDN | self-hosted static files (also fixes offline/proxy issues) |
| Static files | Django dev server | `collectstatic` + WhiteNoise (or nginx) |
| **Media files** | publicly served | **must be login-protected** — generated client reports and templates live here. Use nginx `internal` + `X-Accel-Redirect` (django-sendfile2), not a public `/media/` |
| HTTPS | none | TLS at nginx (internal CA cert), `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS |
| Auth | local passwords | SSO via Azure AD (`mozilla-django-oidc` or `django-allauth`); if local passwords remain: full validator set + `django-axes` login throttling |
| Sessions | default | `SESSION_COOKIE_AGE` ≈ a working day; `SESSION_EXPIRE_AT_BROWSER_CLOSE` per policy |
| Errors | console | Sentry (free tier) or `ADMINS` + email backend; rotating file logs |

Suggested layout: split `settings.py` into `base.py` / `dev.py` / `prod.py`,
read secrets with `django-environ`, and add a `/healthz/` endpoint for monitoring.

## 3. Serving stack

```
nginx (TLS, static, media via X-Accel-Redirect)
  └─ gunicorn, 3 workers (systemd service, auto-restart)
       └─ Django (config.settings.prod)
            └─ PostgreSQL 16 (localhost)
```

`gunicorn config.wsgi -w 3 -b 127.0.0.1:8001 --timeout 60`

## 4. Operations

- **Backups**: nightly `pg_dump` + copy of the media directory to a network
  share; keep 30 days; **test a restore once** before go-live.
- **Scheduled jobs**: cron / systemd timers calling management commands —
  nightly ServiceNow sync, morning DSR auto-draft. No Celery needed at this scale.
- **Monitoring**: uptime ping on `/healthz/`, disk-space alert, Sentry for errors.
- **Patching**: monthly `pip list --outdated` review; apply Django security
  releases promptly; try upgrades on a test instance first.

## 5. Rollout plan

1. Deploy to the VM, import a real ServiceNow CSV, load the real team list.
2. Pilot with yourself + team leads for one week (roster + leaves + one real DSR).
3. Onboard the full team; run old spreadsheets in parallel for two weeks.
4. Cut over; then wire the ServiceNow REST connector and SSO.

## 6. What you explicitly don't need at 60 users

Kubernetes, Redis/Celery, load balancers, CDN, read replicas, microservices.
One VM, Postgres, and backups is the right amount of engineering here.
