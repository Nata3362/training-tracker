# Training Tracker Setup Guide

This guide explains the current repository structure, how to run the project, how the Railway services are configured, and what has been implemented so far.

## 1. Current Scope

Training Tracker is intended to help record training activity, store routines, and follow progression across different disciplines.

The current code includes a React frontend, a FastAPI backend, PostgreSQL storage, and an `Exercise` model. It does not yet implement the complete training tracker product.

### Implemented

- React frontend created with Vite.
- FastAPI backend application.
- PostgreSQL database connection through SQLAlchemy.
- Environment-based database configuration.
- Psycopg 3 connection support for Railway PostgreSQL URLs.
- Automatic creation of SQLAlchemy tables when the backend starts.
- Basic API root and health endpoints.
- Initial `Exercise` database model.
- Initial create and list exercise endpoints.
- Local PostgreSQL service through Docker Compose.
- Frontend and backend deployed as separate Railway services.

### Not implemented yet

- User accounts or authentication.
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
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.css
│   │   ├── App.jsx
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

- `backend/app/main.py` creates the FastAPI application, configures CORS, initializes database tables, and defines the current API endpoints.
- `backend/app/database.py` loads environment variables, reads `DATABASE_URL`, selects the Psycopg 3 SQLAlchemy driver when needed, creates the database engine, and provides database sessions to API handlers.
- `backend/app/models.py` contains the SQLAlchemy models. The current model is `Exercise`.
- `backend/requirements.txt` lists the Python dependencies used by the backend.

### Frontend files

- `frontend/src/main.jsx` is the JavaScript entry point and mounts the React application.
- `frontend/src/App.jsx` contains the current top-level React page and backend status request.
- `frontend/src/App.css` contains component-level styles.
- `frontend/src/index.css` contains global styles.
- `frontend/public/` contains public assets copied into the built frontend.
- `frontend/package.json` defines the npm scripts and frontend dependencies.
- `frontend/package-lock.json` locks the exact npm dependency versions.
- `frontend/vite.config.js` configures Vite and currently uses `/` as the production base path, which is suitable for a Railway domain.

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

### Database initialization

When the backend imports, `main.py` currently runs:

```python
Base.metadata.create_all(bind=engine)
```

This creates tables that do not exist. It means the database must be reachable when the backend starts. This is acceptable for the current prototype, but a future production-ready version should use Alembic migrations instead of relying on import-time table creation.

### Current API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Confirms that the API is running. |
| `GET` | `/health` | Returns the current health response. |
| `GET` | `/docs` | Opens FastAPI's interactive Swagger documentation. |
| `GET` | `/exercises` | Returns exercises stored in the database. |
| `POST` | `/exercises?name=...` | Attempts to create an exercise using the supplied name. |

The current exercise endpoint is only an initial scaffold. The `Exercise` model also contains `discipline` and `metric_type`, so the create endpoint needs to be expanded before exercise creation is considered complete.

The health endpoint currently returns `{"database": true}`. It is a basic response and should later perform an actual database query and return a clear status when the database is unavailable.

## 4. Frontend Design

The frontend is a Vite-powered React application. `frontend/src/main.jsx` mounts `App.jsx` into the `root` element in `frontend/index.html`.

The current page renders:

- The `Training Tracker` heading.
- A backend status label.
- A request to the backend health endpoint.

The frontend is currently a status shell, not a workout management interface. Before Railway deployment, the API request should use the build-time `VITE_API_URL` variable rather than a hard-coded localhost address:

```text
VITE_API_URL=https://YOUR-BACKEND-DOMAIN
```

Vite embeds this value during `npm run build`, so a new frontend deployment is required after changing it in Railway.

The Vite base path is `/`. Railway serves the frontend at the root of its generated domain.

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
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

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

### PostgreSQL service

Create a PostgreSQL service in the Railway project. Railway provides a `DATABASE_URL` variable for it.

Do not copy the real value into source code. Do not put it in the frontend. The backend is the only service that needs direct database access.

### Backend service

Configure the backend Railway service as follows:

- Repository: the training-tracker GitHub repository.
- Root directory: `/backend`.
- Build command: `pip install -r requirements.txt`.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Add this variable to the backend service:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Use the actual PostgreSQL service name in place of `Postgres`. Railway's internal hostname can be used between services in the same project.

Generate a public domain for the backend. Test it with:

```bash
curl https://YOUR-BACKEND-DOMAIN/health
curl https://YOUR-BACKEND-DOMAIN/
```

The backend must listen on `0.0.0.0` and Railway's `$PORT`; otherwise Railway cannot route public traffic to it.

### Frontend service

Configure the frontend Railway service as follows:

- Repository: the same training-tracker GitHub repository.
- Root directory: `/frontend`.
- Build command: `npm ci && npm run build`.
- Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`.

Add this variable to the frontend service:

```text
VITE_API_URL=https://YOUR-BACKEND-DOMAIN
```

Use the public backend domain and include only one `https://` prefix.

Changing a `VITE_*` variable requires a new frontend build because the value is compiled into the JavaScript bundle.

### CORS

The backend currently allows the local frontend origin `http://localhost:5173`. For a deployed frontend, the backend must also allow the exact public frontend Railway origin, for example:

```text
https://YOUR-FRONTEND-DOMAIN
```

If this is not configured, the backend may be reachable directly while browser requests from the frontend are rejected by CORS.

### Railway troubleshooting

If the frontend is blank:

1. Open the frontend deployment logs and confirm a process is listening on `0.0.0.0:$PORT`.
2. Open browser developer tools and check whether JavaScript assets return `200`.
3. Confirm assets are requested from `/assets/`, not `/training-tracker/assets/`.
4. Confirm the browser API request targets the backend Railway domain, not `127.0.0.1` or `localhost`.

If the backend fails during startup:

1. Confirm the service root is `/backend`.
2. Confirm the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Confirm `DATABASE_URL` exists in the backend service variables.
4. Confirm the PostgreSQL service is in the same Railway project.
5. Check that the deployment installed the current `requirements.txt` containing `psycopg`.

## 7. GitHub Collaboration

Never commit:

- `.env` files containing database URLs or passwords.
- `backend/venv/`.
- `frontend/node_modules/`.
- Generated build output or Python cache files.

