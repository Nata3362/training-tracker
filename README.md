# Training Tracker

Training Tracker is a web application for recording training activity and following progression across multiple disciplines.

The repository currently contains the initial application foundation:

- A FastAPI backend connected to PostgreSQL through SQLAlchemy.
- A React frontend built with Vite.
- Local PostgreSQL development through Docker Compose.
- Separate Railway services for the frontend and backend.
- A basic frontend page that checks the backend health endpoint.
- An initial `Exercise` database model and exercise API endpoints.

Workout routines, performed workout logging, progression analytics, dashboards, authentication, and user accounts are planned but are not implemented yet.

## Project Structure

```text
backend/
	app/
		database.py   Database engine, sessions, and environment loading
		main.py       FastAPI application and API endpoints
		models.py     SQLAlchemy database models
	requirements.txt
frontend/
	src/
		App.jsx       Main React component
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
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The local application uses the frontend at `http://localhost:5173` and the API at `http://127.0.0.1:8000`.

See [docs/setup.md](docs/setup.md) for the complete file explanation, local setup, Railway configuration, available endpoints, and current limitations.

## Checks

```bash
cd frontend
npm run lint
npm run build
```

## Deployment

Railway uses two services from this repository:

- Frontend service root: `/frontend`
- Backend service root: `/backend`

The backend needs a Railway PostgreSQL `DATABASE_URL`. The frontend needs the public backend URL in `VITE_API_URL`. Detailed Railway instructions are in [docs/setup.md](docs/setup.md).
