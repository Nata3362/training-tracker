"""Application services for creating and updating person profiles."""

from uuid import UUID

from sqlalchemy.orm import Session

from .models import Person


def create_person(
    db: Session,
    user_id: UUID,
    name: str,
) -> Person:
    """Create and flush a person profile without committing the transaction."""
    person = Person(
        user_id=user_id,
        name=name,
    )
    db.add(person)
    db.flush()
    return person