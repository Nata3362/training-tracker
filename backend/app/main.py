import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import composition

app = FastAPI()

# the deployed frontend is a different origin, so it must be allowed explicitly
# (Railway: CORS_ORIGINS=https://app.<domain>)
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(composition.router)


@app.get("/")
def root():
    return {"message": "Training Tracker API"}


@app.get("/health")
def health():
    return {"database": True}
