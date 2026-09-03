from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Training Tracker API"}


@app.get("/health")
def health():
    return {"database": True}
