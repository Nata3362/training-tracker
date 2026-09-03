# Deployment: Railway

No custom CI/CD pipeline. Railway builds and deploys on every push to `main`
and hosts the Postgres instance too — for two (soon more) users, hand-rolling
GitHub Actions + Docker + a VPS would be solving a problem this app doesn't
have yet.

---

## 1. What Railway hosts

One Railway **project**, two services in it:

- **web** — the FastAPI app, built and deployed straight from this repo.
- **Postgres** — a Railway-managed plugin. Same schema as
  [ARCHITECTURE.md](ARCHITECTURE.md) / [AUTH.md](AUTH.md), nothing
  Railway-specific about it.

```
git push origin main
      │
      ▼
Railway detects the push, builds the web service (Nixpacks)
      │
      ▼
runs the pre-deploy command  →  alembic upgrade head
      │
      ▼
starts the web service        →  uvicorn app.main:app --host 0.0.0.0 --port $PORT
      │
      ▼
live at <project>.up.railway.app (or the custom domain)
```

---

## 2. What the repo needs for Railway to build it

Railway's builder (Nixpacks) auto-detects a Python app from
`pyproject.toml` (or `requirements.txt`) — no Dockerfile needed unless a
system dependency shows up that Nixpacks can't infer, which nothing here
requires. Two settings, in the Railway service's **Settings → Deploy** tab,
not in the repo:

- **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (Railway injects `$PORT`; the app must bind to it, not a hardcoded port.)
- **Pre-deploy command**: `alembic upgrade head` — runs against the new
  release before it takes traffic, so a bad migration fails the deploy
  instead of shipping broken.

---

## 3. Environment variables

- `DATABASE_URL` — not typed in by hand. In Railway, the web service
  references the Postgres plugin's connection string directly
  (`${{Postgres.DATABASE_URL}}` as a service variable), so it rotates
  automatically if the DB's credentials ever change.
- **Nothing else is required for auth.** The session design in
  [AUTH.md](AUTH.md) uses a random opaque token looked up in the `sessions`
  table — it's never signed, so there's no `SECRET_KEY` to provision or
  rotate. One less secret to manage.
- Railway terminates TLS at its edge for every deploy, including the
  default `*.up.railway.app` domain — the `secure=True` cookie flag from
  AUTH.md works without extra setup.

One gotcha worth checking at setup time: Railway's Postgres URL comes as
`postgresql://…`. SQLAlchemy 2.0 with `psycopg` (v3) wants
`postgresql+psycopg://…` — rewrite the scheme when building the engine
(`DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)`) rather
than discovering it as a first-deploy failure.

---

## 4. Domains

Railway issues a free `*.up.railway.app` subdomain automatically. Attach a
real domain later under **Settings → Networking → Custom Domain** — a CNAME
record, TLS is handled for you. Not needed to go live; add when there's a
domain to point.

---

## 5. Rollback

Railway keeps every build. **Deployments** tab → pick a previous one →
**Redeploy** — no separate rollback tooling to build.

---

## 6. Deliberately not set up yet

- **Staging environment / PR previews** — Railway supports both
  (environment cloning, ephemeral per-PR deploys) but that's infrastructure
  for a team reviewing each other's PRs. Add it if a second contributor
  shows up; for now, `main` *is* production.
- **Pre-merge CI checks** (lint, tests) — there's no test suite yet either.
  Once one exists, a GitHub Actions workflow gating merges to `main` is the
  natural next piece; Railway's deploy-on-push stays downstream of it
  unchanged.
- **Backups** — Railway snapshots Postgres on paid plans; confirm the plan
  covers it before there's real logged history worth losing.
