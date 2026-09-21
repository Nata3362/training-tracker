"""Application services for creating and updating person profiles."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from ..authentication.auth import get_user, get_user_optional
from ..authentication.models import User
from ..database import get_db
from .models import Person


def create_person(db: Session, user_id: UUID, name: str) -> Person:
    """Create and flush a person profile without committing the transaction."""
    person = Person(user_id=user_id, name=name)
    db.add(person)
    db.flush()

    return person


def _resolve_person(db: Session, user: User | None) -> Person | None:
    """Resolve a user to their person profile, if one exists."""
    return db.scalar(select(Person).where(Person.user_id == user.id)) if user else None


def get_person(user: User = Depends(get_user), db: Session = Depends(get_db)) -> Person:
    """Resolve the authenticated user's person profile, or raise 401/404."""
    person = _resolve_person(db, user)
    if person is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return person


def get_person_optional(
    user: User | None = Depends(get_user_optional),
    db: Session = Depends(get_db),
) -> Person | None:
    """Resolve the authenticated user's person profile, or None."""
    return _resolve_person(db, user)