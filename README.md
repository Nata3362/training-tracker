# Training Tracker

Training Tracker is a web application for recording training activity and following progression across multiple disciplines.

The repository currently contains the initial application foundation:

- A FastAPI backend connected to PostgreSQL through SQLAlchemy.
- A React frontend built with Vite.
- Local PostgreSQL development through Docker Compose.
- Separate Railway services for the frontend and backend.
- Email and password authentication using server-side sessions in an httpOnly cookie.
- A sign-in and sign-up screen on the frontend.
- Alembic database migrations and a backend test suite.

Workout routines, performed workout logging, progression analytics, and dashboards are planned but are not implemented yet.

## Project Structure

```text
backend/
	app/
		database.py     Database engine, sessions, and environment loading
		main.py         FastAPI application, CORS, and router registration
		models.py       Domain models (Person) — nothing auth-specific
		composition.py  Wires auth + Person together, hosts every /auth/* and /user endpoint
		authentication/ Self-contained auth module — see below
	alembic/        Database migrations
	tests/          Backend test suite
	run_tests.sh    Runs the backend tests
	requirements.txt
frontend/
	src/
		App.jsx       Top-level component, switches on auth state
		AuthForm.jsx  Sign-in and sign-up form
		auth.jsx      AuthProvider, holds the current user
		authContext.js  Auth context and the useAuth hook
		api.js        fetch wrapper that sends the session cookie
		main.jsx      React entry point
		*.css         Frontend styling
	package.json    Frontend scripts and dependencies
	vite.config.js  Vite configuration
docker-compose.yml Local PostgreSQL service
docs/setup.md     Detailed setup and architecture guide
```

## Quick Start

Start PostgreSQL:

```bash
docker compose up -d database
```

Start the backend in a separate terminal:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

`alembic upgrade head` creates the database tables. It is required on a fresh
database — the application no longer creates tables on startup.

Start the frontend in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The local application uses the frontend at `http://localhost:5173` and the API at `http://localhost:8000`.

Use `localhost` for the API, not `127.0.0.1`. The browser treats them as different
sites, and the session cookie would be dropped.

See [docs/setup.md](docs/setup.md) for the complete file explanation, local setup, Railway configuration, available endpoints, and current limitations.

## Checks

```bash
cd frontend
npm run lint
npm run build
```

```bash
cd backend
./run_tests.sh
```

## Deployment

Railway uses two services from this repository:

- Frontend service root: `/frontend`
- Backend service root: `/backend`

The deploy commands live in `backend/railway.json` and `frontend/railway.json`,
so only each service's root directory and its variables are set in the dashboard.

The backend needs a Railway PostgreSQL `DATABASE_URL` and the allowed frontend origin in `CORS_ORIGINS`. The frontend needs the public backend URL in `VITE_API_URL`.

The application is served from `https://www.natoli.dk`, the API from
`https://api.natoli.dk`, and `natoli.dk` redirects to the former. Both services
must share one registrable domain: the generated `*.up.railway.app` domains do
not work for a logged-in session, because they count as separate sites and the
browser discards the session cookie. Detailed Railway instructions are in
[docs/DEPLOY.md](docs/DEPLOY.md).
