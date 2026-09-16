import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from .account import routes as account_routes
from .person import routes as person_routes
from .authentication import routes as authentication_routes

from .database import get_db

app = FastAPI()

# the deployed frontend is a different origin, so it must be allowed explicitly
# (Railway: CORS_ORIGINS=https://www.natoli.dk)
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(person_routes.router)
app.include_router(account_routes.router)
app.include_router(authentication_routes.router)


@app.get("/")
def root():
    return {"message": "Training Tracker API"}


@app.get("/health")
def health(db: DBSession = Depends(get_db)):
    # Railway's healthcheck hits this, so it has to actually touch the database:
    # a reply of "healthy" from a service that can't reach Postgres would let a
    # broken release take traffic. A failed query raises, which is the point.
    db.execute(text("SELECT 1"))
    return {"database": True}
