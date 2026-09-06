# Deployment: Railway

No custom CI/CD pipeline. Railway builds and deploys on every push to `main`
and hosts the Postgres instance too — for two (soon more) users, hand-rolling
GitHub Actions + Docker + a VPS would be solving a problem this app doesn't
have yet.

---

## 1. What Railway hosts

One Railway **project**, three services in it:

- **backend** — the FastAPI app (service root `/backend`), built and deployed
  straight from this repo.
- **frontend** — the React/Vite app (service root `/frontend`), built with
  `npm ci && npm run build` and served by `npm run preview`.
- **Postgres** — a Railway-managed plugin. Same schema as
  [ARCHITECTURE.md](ARCHITECTURE.md) / [AUTH.md](AUTH.md), nothing
  Railway-specific about it.

The two app services must be reached through subdomains of one custom domain
or logged-in sessions do not work at all — see §4, which is now a requirement
rather than the "add it later" it used to be.

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
- **No secret is required for auth.** The session design in
  [AUTH.md](AUTH.md) uses a random opaque token looked up in the `sessions`
  table — it's never signed, so there's no `SECRET_KEY` to provision or
  rotate. One less secret to manage.
- `CORS_ORIGINS` — on the backend service, the frontend's exact origin
  (`https://app.<domain>`, no trailing slash; comma-separated for several).
  Defaults to `http://localhost:5173`, so the deployed frontend can't call the
  API until this is set.
- `VITE_API_URL` — on the frontend service, `https://api.<domain>`. Vite bakes
  it into the bundle at build time, so changing it needs a rebuild, not just a
  restart.
- Railway terminates TLS at its edge for every deploy, including the
  default `*.up.railway.app` domain — the `secure=True` cookie flag from
  AUTH.md works without extra setup.

One gotcha worth checking at setup time: Railway's Postgres URL comes as
`postgresql://…`. SQLAlchemy 2.0 with `psycopg` (v3) wants
`postgresql+psycopg://…` — rewrite the scheme when building the engine
(`DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)`) rather
than discovering it as a first-deploy failure.

---

## 4. Domains — required, not optional

Railway issues a free `*.up.railway.app` subdomain per service, and for this
app **they are not usable together**. Railway lists `up.railway.app` on the
[Public Suffix List](https://publicsuffix.org/), so a browser treats
`frontend-x.up.railway.app` and `backend-y.up.railway.app` as *separate
sites*. The session cookie from [AUTH.md](AUTH.md) is `SameSite=Lax`, and a
browser refuses to store such a cookie arriving from another site: login
returns `200`, nothing is kept, every later request is anonymous. No code
change fixes this — it's the browser enforcing the PSL.

One registrable domain across both services fixes it:

- `app.<domain>` → frontend service
- `api.<domain>` → backend service

Same registrable domain (`<domain>`) means same site, and `Lax` behaves as
designed.

Per service: **Settings → Networking → Public Networking → Custom Domain**,
then add the **CNAME *and* TXT records** Railway displays — both are required.
TLS is issued and renewed automatically. Use subdomains, not the apex: an apex
domain can't hold a CNAME in ordinary DNS and needs provider-specific
ALIAS/ANAME support. On Cloudflare, check Railway's current guidance before
enabling the orange-cloud proxy.

`ponytail: a ~$10/yr domain instead of collapsing to one service and writing
build config — DNS does the work.`

A native mobile app, if it happens, is unaffected by any of this (`SameSite`
is a browser rule), but benefits from the same domain: a shipped binary
pointing at `api.<domain>` survives moving off Railway, one pointing at a
generated hostname doesn't.

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
