# Training Tracker Setup Guide

This guide explains the current repository structure, how to run the project, how the Railway services are configured, and what has been implemented so far.

## 1. Current Scope

Training Tracker is intended to help record training activity, store routines, and follow progression across different disciplines.

The current code includes a React frontend, a FastAPI backend, PostgreSQL storage, and email and password authentication. It does not yet implement the complete training tracker product.

### Implemented

- React frontend created with Vite.
- FastAPI backend application.
- PostgreSQL database connection through SQLAlchemy.
- Environment-based database configuration.
- Psycopg 3 connection support for Railway PostgreSQL URLs.
- Alembic migrations, which own the database schema.
- Basic API root and health endpoints.
- User accounts with scrypt password hashing.
- Server-side sessions delivered in an httpOnly cookie.
- Signup, login, logout, and current-user endpoints.
- A sign-in and sign-up screen, and session restore on page load.
- A backend test suite covering the authentication endpoints.
- Local PostgreSQL service through Docker Compose.
- Frontend and backend deployed as separate Railway services.

### Not implemented yet

- Friends, teams, or shared training groups.
- Workout templates or saved routines.
- Creating a workout while training.
- Recording performed workouts and individual sets.
- Exercise progression calculations or charts.
- Weekly or monthly dashboard summaries.
- A multiple-discipline user interface.
- Mobile-specific screens or a responsive training workflow.

These should be added in separate feature slices after the current foundation is stable.

## 2. Repository Structure

```text
training-tracker/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── authentication/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   └── security.py
│   │   ├── __init__.py
│   │   ├── composition.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   └── test_composition.py
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── run_tests.sh
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── api.js
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── auth.jsx
│   │   ├── authContext.js
│   │   ├── AuthForm.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── docker-compose.yml
├── README.md
└── docs/
    └── setup.md
```

### Root files

- `README.md` is the short project overview and quick-start page.
- `docker-compose.yml` defines the local PostgreSQL container.
- `.gitignore` prevents local environment files, virtual environments, dependencies, and generated files from being committed.
- `docs/setup.md` is this detailed setup and architecture guide.

### Backend files

- `backend/app/main.py` creates the FastAPI application, configures CORS from `CORS_ORIGINS`, and registers `composition.router`.
- `backend/app/database.py` loads environment variables, reads `DATABASE_URL`, selects the Psycopg 3 SQLAlchemy driver when needed, creates the database engine, and provides database sessions to API handlers.
- `backend/app/models.py` contains the domain models — currently just `Person`. Nothing auth-specific lives here.
- `backend/app/composition.py` is the only file that imports both `app.authentication` and `app.models`, **and it is where every endpoint lives** — `app/authentication/` defines no routes at all, only plain functions. Every route handler (`/auth/signup`, `/auth/login`, `/auth/logout`, `/user`) calls into `app.authentication.auth`'s functions; `signup_endpoint` and `user_endpoint` additionally touch `Person` directly (creating it, or joining it in), since each has exactly one caller and isn't worth a separate function.
- `backend/app/authentication/` is a self-contained module that knows only about `users` and `sessions`, not about people or workouts, and defines no HTTP endpoints:
  - `models.py` — the `User` and `AuthSession` SQLAlchemy models.
  - `security.py` — hashes and verifies passwords using `hashlib.scrypt` from the standard library.
  - `auth.py` — plain functions: `create_user`, `authenticate_user`, `create_session`/`verify_session`/`revoke_session`, and the `require_auth` dependency that protected endpoints depend on.
  - `schemas.py` — the Pydantic request bodies (`SignupBody`, `LoginBody`).
- `backend/alembic/` contains the migrations that create and change the database schema.
- `backend/tests/` contains the test suite, and `run_tests.sh` runs it.
- `backend/requirements.txt` lists the Python dependencies used by the backend.

### Frontend files

- `frontend/src/main.jsx` is the JavaScript entry point and mounts the React application inside the authentication provider.
- `frontend/src/App.jsx` is the top-level page. It shows the sign-in form when logged out and a placeholder shell when logged in.
- `frontend/src/AuthForm.jsx` is the combined sign-in and sign-up form.
- `frontend/src/auth.jsx` holds the current user, and calls the backend to log in, sign up, and log out.
- `frontend/src/authContext.js` contains the auth context and the `useAuth` hook.
- `frontend/src/api.js` wraps `fetch`, sets the API base URL, sends the session cookie, and turns error responses into exceptions.
- `frontend/src/App.css` contains component-level styles.
- `frontend/src/index.css` contains global styles.
- `frontend/public/` contains public assets copied into the built frontend.
- `frontend/package.json` defines the npm scripts and frontend dependencies.
- `frontend/package-lock.json` locks the exact npm dependency versions.
- `frontend/vite.config.js` configures Vite: `/` as the production base path, and `preview.allowedHosts` so the deployed preview server accepts the custom domain.

## 3. Backend Design

The backend currently uses this simple flow:

```text
HTTP request
    -> FastAPI endpoint in app/main.py
    -> SQLAlchemy session from app/database.py
    -> PostgreSQL database
    -> JSON response
```

### Database configuration

`backend/app/database.py` reads the database connection from the environment:

```python
DATABASE_URL = os.getenv("DATABASE_URL")
```

Railway supplies the real value through the backend service environment. The code changes a URL beginning with `postgresql://` to `postgresql+psycopg://` so SQLAlchemy uses the installed Psycopg 3 driver instead of looking for `psycopg2`.

The real database URL must never be committed to GitHub. For Railway, set the backend service variable using a Railway reference similar to:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Replace `Postgres` with the exact name of the PostgreSQL service in the Railway project.

For local development, use a separate ignored file at `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/training_tracker
```

The local value must match the PostgreSQL service configured in `docker-compose.yml`.

### Database migrations

The schema is owned by Alembic. The application no longer creates tables when it
starts, so a fresh database needs:

```bash
cd backend
alembic upgrade head
```

Alembic reads the same `DATABASE_URL` as the application: `alembic/env.py` imports
it from `app.database`, so the connection is configured in one place and
`alembic.ini` holds no database URL. It also imports `app.composition` rather than
either model module directly — that one import pulls in both `app.models`
(`Person`) and `app.authentication.models` (`User`, `AuthSession`), so every table
registers on `Base.metadata` regardless of which module it's declared in.

After changing a model — `backend/app/models.py` or
`backend/app/authentication/models.py` — generate a migration and apply it:

```bash
alembic revision --autogenerate -m "short description"
alembic upgrade head
```

Always read the generated file before applying it. Autogenerate detects most
changes but not all of them.

On Railway, run `alembic upgrade head` as the backend service's pre-deploy command,
so a failed migration fails the deployment instead of starting a broken release.

### Current API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Confirms that the API is running. |
| `GET` | `/health` | Runs `SELECT 1` and returns `{"database": true}`. |
| `GET` | `/docs` | Opens FastAPI's interactive Swagger documentation. |
| `POST` | `/auth/signup` | Creates a user and a person, and starts a session. Returns `409` if the email is taken. |
| `POST` | `/auth/login` | Starts a session. Returns `401` for a wrong email or password. |
| `POST` | `/auth/logout` | Revokes the current session and clears the cookie. |
| `GET` | `/user` | Returns the signed-in user: `{id, email, name}`. Returns `401` when not signed in. |

The health endpoint executes `SELECT 1` before replying `{"database": true}`, so
it fails rather than reporting healthy when the database is unreachable. Railway
uses it as the backend service's healthcheck path, which is why it has to touch
the database: a release that can't reach Postgres must not take traffic.

### Authentication

Login creates a row in the `sessions` table and returns a random token in a cookie.
The table stores only a SHA-256 hash of that token, so a leaked table does not hand
out working logins. Passwords are hashed with `hashlib.scrypt`.

The cookie is set `HttpOnly` (JavaScript cannot read it), `Secure` (HTTPS only), and
`SameSite=Lax`. Because JavaScript cannot read the cookie, the frontend calls
`GET /user` on page load to find out whether it is signed in.

Endpoints that need a signed-in user depend on `require_auth`, which returns the
user id or raises `401`:

```python
@router.get("/example")
def example(user_id: int = Depends(require_auth)):
    ...
```

`SameSite=Lax` is also the reason both services must sit under one custom domain.
See section 6.

`GET /user` lives in `app/composition.py`, not `app/authentication/` — that
module defines no endpoints at all, just the plain functions `user_endpoint`
calls into (`require_auth`). It joins `User` and `Person` directly for the
`name` the frontend displays — a one-off join, not worth its own named
function for a single caller. An earlier pass also had a pure
`app.authentication`-only `/auth/me` (`{id, email}`, no `Person`) alongside
this one; it was removed as redundant for an app with a single frontend
consumer — nothing needed "logged in, but no name" as a separate case. If
that need shows up later (a consumer that must stay ignorant of the domain
schema), a small `get_auth_identity()` wrapping `db.get(User, user_id)` is
the way back in.

## 4. Frontend Design

The frontend is a Vite-powered React application. `frontend/src/main.jsx` mounts `App.jsx` into the `root` element in `frontend/index.html`.

`AuthProvider` in `src/auth.jsx` calls `GET /user` once when the application
loads. While that request is in flight the page renders nothing; afterwards it
renders either the sign-in form or the signed-in shell. Signing in or signing up
re-fetches the user, so the shell appears without a page reload.

Every request goes through `api()` in `src/api.js`, which sets
`credentials: "include"`. Without it the browser would neither store nor send the
session cookie, and every request would be anonymous.

The frontend is otherwise still a shell, not a workout management interface. The API
base URL comes from the build-time `VITE_API_URL` variable rather than a hard-coded
address:

```text
VITE_API_URL=https://api.natoli.dk
```

Vite embeds this value during `npm run build`, so a new frontend deployment is required after changing it in Railway.

The Vite base path is `/`. Railway serves the frontend at the root of its domain.

## 5. Local Development

### Prerequisites

Install the following tools:

- Git
- Python 3.12 or newer
- Node.js and npm
- Docker Desktop or Docker Engine with Compose

### Start PostgreSQL

From the repository root:

```bash
docker compose up -d database
```

Check the container status:

```bash
docker compose ps
```

Stop the database when finished:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local database volume and all local data.

### Start the backend

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

Use `localhost` rather than `127.0.0.1`. The browser treats the two as different
sites, so a session cookie set by one is not sent from a page served by the other,
and every request after signing in would be anonymous. `frontend/.env` should
therefore contain:

```env
VITE_API_URL=http://localhost:8000
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\venv\Scripts\Activate.ps1
```

### Start the frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server normally runs at:

`http://localhost:5173/`

### Backend tests

```bash
cd backend
./run_tests.sh
```

The tests run against an in-memory SQLite database, so PostgreSQL does not need to
be running and the local database is never touched. `tests/conftest.py` swaps the
`get_db` dependency for a test session, and uses an `https` test client so the
`Secure` session cookie is kept.

Pass any pytest arguments through the script, for example `./run_tests.sh -k login`.

### Frontend checks

Run the linter:

```bash
cd frontend
npm run lint
```

Create a production build:

```bash
cd frontend
npm run build
```

Preview the production build locally:

```bash
cd frontend
npm run preview -- --host 0.0.0.0 --port 4173
```

## 6. Railway Deployment

The project uses two Railway application services connected to the same GitHub repository, plus a Railway PostgreSQL service.

Both application services must be reachable through one shared registrable
domain. This is a requirement, not a preference — see "Custom domain" below.
The deployed application lives at `https://www.natoli.dk`, the API at
`https://api.natoli.dk`.

### PostgreSQL service

Create a PostgreSQL service in the Railway project. Railway provides a `DATABASE_URL` variable for it.

Do not copy the real value into source code. Do not put it in the frontend. The backend is the only service that needs direct database access.

### Backend service

Configure the backend Railway service as follows:

- Repository: the training-tracker GitHub repository.
- Root directory: `/backend`.

The build command is inferred from `requirements.txt`. The start command,
pre-deploy command and healthcheck path come from `backend/railway.json` in the
repository, which overrides the dashboard — they do not need to be entered by
hand:

- Pre-deploy command: `alembic upgrade head`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Healthcheck path: `/health` (runs `SELECT 1`).

Add these variables to the backend service:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=https://www.natoli.dk
```

`CORS_ORIGINS` is the exact origin of the frontend, including the scheme and with
no trailing slash. Several origins can be given, separated by commas. If it is not
set, only `http://localhost:5173` is allowed and the deployed frontend cannot call
the API.

Use the actual PostgreSQL service name in place of `Postgres`. Railway's internal hostname can be used between services in the same project.

Generate a public domain for the backend. Test it with:

```bash
curl https://api.natoli.dk/health
curl https://api.natoli.dk/
```

The backend must listen on `0.0.0.0` and Railway's `$PORT`; otherwise Railway cannot route public traffic to it.

### Frontend service

Configure the frontend Railway service as follows:

- Repository: the same training-tracker GitHub repository.
- Root directory: `/frontend`.

`npm ci && npm run build` is inferred from `package.json`, and the start command
(`npm run preview`) comes from `frontend/railway.json`. The `preview` script
itself binds `--host 0.0.0.0 --port ${PORT:-4173}`; both flags are required for
Railway to route traffic to it, and the fallback keeps the script usable locally.

`frontend/vite.config.js` also sets `preview.allowedHosts` to `['.natoli.dk']`.
Vite's preview server rejects any request whose `Host` header is not listed,
answering `Blocked request. This host is not allowed`, so the custom domain must
be named there. The leading dot covers the apex and every subdomain.

Add this variable to the frontend service:

```text
VITE_API_URL=https://api.natoli.dk
```

Include only one `https://` prefix.

Changing a `VITE_*` variable requires a new frontend build because the value is compiled into the JavaScript bundle.

### Custom domain

The generated `*.up.railway.app` domains cannot carry a logged-in session. Railway
lists `up.railway.app` on the Public Suffix List, so the browser treats
`frontend-x.up.railway.app` and `backend-y.up.railway.app` as separate sites. The
session cookie is `SameSite=Lax`, and a browser refuses to store such a cookie that
arrives from another site. Signing in returns `200`, no cookie is kept, and every
following request is anonymous. Nothing in the code can work around this.

Putting both services under one registrable domain fixes it:

- `www.natoli.dk` for the frontend service.
- `api.natoli.dk` for the backend service.

Both are then the same site, and the cookie behaves as intended. They remain
different *origins*, so CORS still applies — the two checks are independent.

For each service, open **Settings → Networking → Public Networking → Custom
Domain**, enter the subdomain, and add the **CNAME and TXT records** Railway
displays. Both records are required; without the TXT record the domain resolves
but returns `404`. Railway issues and renews the TLS certificate automatically.

DNS for `natoli.dk` is at Simply.com:

```text
www   CNAME  <frontend-service>.up.railway.app
api   CNAME  <backend-service>.up.railway.app
+ the two TXT verification records Railway shows
```

The bare domain is handled by Simply.com's URL forwarding, set under the
domain's DNS administration: `natoli.dk` → `https://www.natoli.dk`. It is free
and the forwarding server issues its own certificate, so `https://natoli.dk`
redirects instead of failing on a certificate mismatch.

The bare domain cannot point at Railway directly. Railway hands out a CNAME
target, a CNAME is illegal at a zone apex, and the workarounds (ALIAS/ANAME
records, CNAME flattening) are provider features Simply.com does not offer.
Reaching the apex would mean moving the domain's nameservers to a provider that
does, such as Cloudflare — see [DEPLOY.md](DEPLOY.md) §4, which also covers the
`.dk` registry's validation rules for that. It buys nothing for this app.

### CORS

CORS and the cookie rules above are separate checks, and both have to pass. CORS
decides whether the frontend's JavaScript may read the response; `SameSite` decides
whether the browser keeps and sends the cookie at all. Correct CORS with a
cross-site cookie still leaves every request anonymous.

The backend allows the origins in `CORS_ORIGINS`, defaulting to
`http://localhost:5173`. Credentials are enabled, which is why the origin has to be
listed exactly — a wildcard is not permitted for credentialed requests.

### Railway troubleshooting

If the frontend is blank:

1. Open the frontend deployment logs and confirm a process is listening on `0.0.0.0:$PORT`.
   If the page instead reads `Blocked request. This host is not allowed`, the
   hostname is missing from `preview.allowedHosts` in `frontend/vite.config.js`.
2. Open browser developer tools and check whether JavaScript assets return `200`.
3. Confirm assets are requested from `/assets/`, not `/training-tracker/assets/`.
4. Confirm the browser API request targets the backend custom domain (`api.natoli.dk`), not `127.0.0.1`, `localhost`, or the generated `*.up.railway.app` domain.

If the backend fails during startup:

1. Confirm the service root is `/backend`.
2. Confirm the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (it comes from `backend/railway.json`).
3. Confirm `DATABASE_URL` exists in the backend service variables.
4. Confirm the PostgreSQL service is in the same Railway project.
5. Check that the deployment installed the current `requirements.txt` containing `psycopg`.
6. Check the pre-deploy logs for a failed `alembic upgrade head`.

If signing in appears to succeed but the user is immediately signed out again:

1. Confirm both services are being used through the custom domain, not the
   generated `*.up.railway.app` domains.
2. In the browser's developer tools, check whether a `session` cookie was stored
   for the API subdomain after signing in. If not, the domains are not same-site.
3. Confirm `CORS_ORIGINS` matches the frontend origin exactly.
4. Confirm the frontend was rebuilt after `VITE_API_URL` was changed.

## 7. GitHub Collaboration

Never commit:

- `.env` files containing database URLs or passwords.
- `backend/venv/`.
- `frontend/node_modules/`.
- Generated build output or Python cache files.

