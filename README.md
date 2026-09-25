# Training Tracker

Training Tracker is a web application for recording training activity and following progression across multiple disciplines.

The repository currently contains:

- A FastAPI backend connected to PostgreSQL through SQLAlchemy.
- A React frontend built with Vite and React Router.
- Local PostgreSQL development through Docker Compose.
- Separate Railway services for the frontend and backend.
- Email and password authentication using server-side sessions in an httpOnly cookie.
- A sign-in and sign-up screen on the frontend.
- A per-user exercise library: create, edit, delete, and list exercises, seeded
  with a set of default exercises. It has a backend API and a frontend page.
- Alembic database migrations and a backend test suite.

Creating workouts and logging performed workouts are in progress: the frontend
pages exist as placeholders. Progression analytics and dashboards are planned.
See [docs/Design/Requirements.md](docs/Design/Requirements.md) for the intended
workout model.

## Project Structure

```text
backend/
	app/
		main.py         FastAPI application, CORS, router registration, /health
		database.py     Database engine, sessions, and environment loading
		authentication/ Self-contained auth module: users, sessions, password hashing, GET /user
		account/        /account/* endpoints: signup, login, logout (creates User + Person)
		person/         Person profile model and GET /person/me
		exercise/       Exercise model, /exercise/* CRUD endpoints, default exercise seeding
	alembic/        Database migrations
	tests/          Backend test suite
	run_tests.sh    Runs the backend tests
	requirements.txt
frontend/
	src/
		main.jsx      React entry point
		api.js        fetch wrapper that sends the session cookie
		app/          App shell, layout, home page, and routes
		features/
			auth/       Sign-in/sign-up form, AuthProvider, and useAuth hook
			exercises/  Exercise library, create workout, and perform workout pages
		*.css         Frontend styling
	package.json    Frontend scripts and dependencies
	vite.config.js  Vite configuration
docker-compose.yml Local PostgreSQL service
docs/
	setup.md        Detailed setup guide
	ARCHITECTURE.md Architecture overview
	AUTH.md         Authentication design
	DEPLOY.md       Railway deployment
	Design/         Requirements and design material
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

See [docs/setup.md](docs/setup.md) for the complete local setup, Railway configuration, available endpoints, and current limitations.

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
