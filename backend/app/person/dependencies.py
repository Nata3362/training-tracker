"""FastAPI dependencies for resolving the authenticated person's profile."""

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..authentication.auth import require_auth
from ..database import get_db
from .models import Person


def require_person(
        user_id: uuid.UUID | None = Depends(require_auth), 
        db: Session = Depends(get_db)
) -> Person:
    """Return the current person's profile or raise a not-found error."""
    person = db.scalar(
        select(Person).where(Person.user_id == user_id)
    )

    if person is None:
        raise HTTPException(
            status_code=404,
             detail= "Person profile not found")

    return person
    
