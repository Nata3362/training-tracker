# Deployment: Railway

No custom CI/CD pipeline. Railway builds and deploys on every push to `main`
and hosts the Postgres instance too — for two (soon more) users, hand-rolling
GitHub Actions + Docker + a VPS would be solving a problem this app doesn't
have yet.

The live application:

| What | Where |
| ---- | ----- |
| Frontend | `https://www.natoli.dk` |
| Backend API | `https://api.natoli.dk` |
| Bare domain | `natoli.dk` → redirects to `https://www.natoli.dk` |

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

The two app services must share one registrable domain or logged-in sessions
do not work at all — see §4. That is a hard requirement, not a nicety.

```
git push origin main
      │
      ▼
Railway detects the push, builds the service (Railpack)
      │
      ▼
runs the pre-deploy command  →  alembic upgrade head
      │
      ▼
starts the service            →  uvicorn app.main:app --host 0.0.0.0 --port $PORT
      │
      ▼
live at https://api.natoli.dk
```

---

## 2. What the repo already carries

Railway's builder auto-detects a Python app from `requirements.txt` and a Node
app from `package.json` — no Dockerfile needed unless a system dependency shows
up that the builder can't infer, which nothing here requires.

The deploy commands live in the repo rather than in dashboard fields, as
`backend/railway.json` and `frontend/railway.json`. Railway reads the file from
the service's root directory, and **configuration defined in code overrides the
dashboard** — so these are the source of truth and there is nothing to re-type
if a service is ever recreated.

`backend/railway.json`:

- **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (Railway injects `$PORT`; the app must bind to it, not a hardcoded port.)
- **Pre-deploy command**: `alembic upgrade head` — runs against the new
  release before it takes traffic, so a bad migration fails the deploy
  instead of shipping broken.
- **Healthcheck path**: `/health`. The endpoint runs `SELECT 1`, so a release
  that can't reach Postgres fails the healthcheck instead of taking traffic.

`frontend/railway.json` just sets the start command to `npm run preview`. The
`preview` script itself carries the flags that matter:

```json
"preview": "vite preview --host 0.0.0.0 --port ${PORT:-4173}"
```

Both halves are load-bearing. Without `--host 0.0.0.0` Vite binds loopback only
and Railway's healthcheck can never reach it; without `--port $PORT` it ignores
the port Railway assigned. The `:-4173` fallback keeps `npm run preview` working
locally, where `$PORT` is unset.

The one thing that is *not* in the repo, because Railway offers no config-as-code
field for it: each service's **Root Directory** (`/backend`, `/frontend`), set
under Settings → Source.

### Vite blocks unknown hosts

`frontend/vite.config.js` sets:

```js
preview: { allowedHosts: ['.natoli.dk'] }
```

Since Vite 6, the preview server rejects any request whose `Host` header isn't
listed, answering `Blocked request. This host is not allowed` — which looks like
a DNS or Railway fault but isn't. The leading dot allows the apex and every
subdomain, so `www.natoli.dk` is covered and so is anything added later.

---

## 3. Environment variables

- `DATABASE_URL` — not typed in by hand. In Railway, the backend service
  references the Postgres plugin's connection string directly
  (`${{Postgres.DATABASE_URL}}` as a service variable), so it rotates
  automatically if the DB's credentials ever change.
- **No secret is required for auth.** The session design in
  [AUTH.md](AUTH.md) uses a random opaque token looked up in the `sessions`
  table — it's never signed, so there's no `SECRET_KEY` to provision or
  rotate. One less secret to manage.
- `CORS_ORIGINS` — on the backend service, `https://www.natoli.dk` (exact
  origin, no trailing slash; comma-separated for several). Defaults to
  `http://localhost:5173`, so the deployed frontend can't call the API until
  this is set.
- `VITE_API_URL` — on the frontend service, `https://api.natoli.dk`. Vite bakes
  it into the bundle at build time, so changing it needs a rebuild, not just a
  restart.
- Railway terminates TLS at its edge for every deploy, so the `secure=True`
  cookie flag from AUTH.md works without extra setup.

Railway's Postgres URL comes as `postgresql://…`, and SQLAlchemy 2.0 with
`psycopg` (v3) wants `postgresql+psycopg://…`. `app/database.py` rewrites the
scheme on the way in, so the plugin's variable can be referenced as-is.

That same module sets `pool_pre_ping=True`: Railway reaps idle Postgres
connections, and without it the first request after a quiet period fails on a
dead connection instead of transparently reconnecting.

---

## 4. Domains — required, not optional

Railway issues a free `*.up.railway.app` subdomain per service, and for this
app **they are not usable together**. Railway lists `up.railway.app` on the
[Public Suffix List](https://publicsuffix.org/), so a browser treats
`frontend-x.up.railway.app` and `backend-y.up.railway.app` as *separate
sites*. The session cookie from [AUTH.md](AUTH.md) is `SameSite=Lax`, and a
browser refuses to send such a cookie on a cross-site request: login returns
`200`, and every later request is anonymous. No code change fixes this — it's
the browser enforcing the PSL.

The requirement is one shared **registrable domain**, not any particular shape
of hostname. Different subdomains of `natoli.dk` are different *origins* (so
CORS still applies, hence `CORS_ORIGINS`) but the same *site*, which is what
`SameSite=Lax` actually cares about:

- `www.natoli.dk` → frontend service
- `api.natoli.dk` → backend service

### DNS at Simply.com

Per service: **Settings → Networking → Public Networking → Custom Domain**,
then add the **CNAME *and* TXT records** Railway displays — both are required.
If the TXT record is missing, the domain resolves but every request returns
`404`. TLS is issued and renewed automatically.

```
www   CNAME  <frontend-service>.up.railway.app
api   CNAME  <backend-service>.up.railway.app
+ the two TXT verification records Railway shows
```

Then, under the domain's DNS administration, set **URL forwarding**:
`natoli.dk` → `https://www.natoli.dk`. It's free, and Simply's forwarding
server issues its own certificate, so someone typing `https://natoli.dk`
is redirected rather than met with a certificate error.

### Why not the apex directly

`natoli.dk` itself can't point at Railway from Simply.com. Railway hands out a
CNAME target, a CNAME is illegal at a zone apex, and the escape hatches
(ALIAS/ANAME records, CNAME flattening) are provider features Simply.com does
not offer — their DNS supports A, AAAA, CNAME, MX, TXT, NS and SRV, and their
docs state CNAMEs only work on subdomains.

Getting the app onto the bare domain would mean moving the domain's
nameservers to a provider with CNAME flattening (Cloudflare being the usual
choice; registration would stay at Simply.com). Worth knowing the option
exists, but it buys nothing here: `www.natoli.dk` and `natoli.dk` are the same
site as far as the session cookie is concerned, and the URL forwarding already
makes the bare domain work for anyone who types it.

Note for whoever tries it anyway: Punktum.dk validates a `.dk` nameserver
change by querying the new nameservers, which must already answer
authoritatively for the domain. The zone has to exist at the new provider
*before* the change is submitted, or the registry rejects it.

`ponytail: a ~$10/yr domain and two CNAMEs instead of collapsing to one service
and writing build config — DNS does the work.`

A native mobile app, if it happens, is unaffected by any of this (`SameSite`
is a browser rule), but benefits from the same domain: a shipped binary
pointing at `api.natoli.dk` survives moving off Railway, one pointing at a
generated hostname doesn't.

---

## 5. First deploy, in order

1. Create the Railway project and add the **Postgres** plugin first, so its
   variable exists to reference.
2. Add the **backend** service from this repo, set Root Directory `/backend`,
   set `DATABASE_URL` to `${{Postgres.DATABASE_URL}}`. It will deploy and run
   `alembic upgrade head` on the way up.
3. Add the **frontend** service from the same repo, Root Directory `/frontend`.
4. Add the custom domains to each service and create the DNS records at
   Simply.com. Wait for both to verify.
5. Only now set `CORS_ORIGINS` on the backend and `VITE_API_URL` on the
   frontend — both need the final hostnames — and redeploy the frontend so the
   API URL is baked into a fresh bundle.
6. Sign up once through `https://www.natoli.dk` and confirm the session
   survives a page reload. That single check exercises the whole chain: DNS,
   TLS, CORS, and the same-site cookie.

---

## 6. Rollback

Railway keeps every build. **Deployments** tab → pick a previous one →
**Redeploy** — no separate rollback tooling to build.

---

## 7. Deliberately not set up yet

- **Staging environment / PR previews** — Railway supports both
  (environment cloning, ephemeral per-PR deploys) but that's infrastructure
  for a team reviewing each other's PRs. Add it if a second contributor
  shows up; for now, `main` *is* production.
- **Pre-merge CI checks** — the backend suite (`backend/run_tests.sh`) and the
  frontend's `npm run lint && npm run build` both exist now, so a GitHub
  Actions workflow gating merges to `main` is the natural next piece;
  Railway's deploy-on-push stays downstream of it unchanged.
- **Backups** — Railway snapshots Postgres on paid plans; confirm the plan
  covers it before there's real logged history worth losing.
