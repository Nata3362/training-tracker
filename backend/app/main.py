from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, get_db
from . import models


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Training Tracker API"}


@app.get("/health")
def health():
    return {"database": True}

@app.post("/exercises")
def create_exercise(
    name: str,
    db: Session = Depends(get_db),
):
    exercise = models.Exercise(name=name)

    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    return exercise

@app.get("/exercises")
def get_exercises(db: Session = Depends(get_db)):
    return db.query(models.Exercise).all()