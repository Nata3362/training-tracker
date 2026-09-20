"""Application services for creating and updating person profiles."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from ..authentication.auth import get_user
from ..authentication.models import User
from ..database import get_db
from .models import Person


def create_person(db: Session, user_id: UUID, name: str) -> Person:
    """Create and flush a person profile without committing the transaction."""
    person = Person(user_id=user_id, name=name)
    db.add(person)
    db.flush()

    return person


def get_person(required: bool = True):
    """Build a dependency resolving the authenticated user's person profile.

    Args:
        required: when True (default), raise 401/404 instead of returning None.

    """
    def dependency(
        user: User | None = Depends(get_user(required=required)),
        db: Session = Depends(get_db),
    ) -> Person | None:

        person = db.scalar(select(Person).where(Person.user_id == user.id)) if user else None

        if required and person is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return person

    return dependency