# Create User and Person 
import uuid

from sqlalchemy.orm import Session
from ..authentication.auth import create_session, create_user, authenticate_user
from ..person.service import create_person


def register_account(
    db: Session,
    email: str,
    password: str,
    name: str, 
) -> str:
    user = create_user(db ,email, password)
    person = create_person(db, user.id, name)
    token = create_session(db, user.id)
    db.commit()

    return token


def login_user(db: Session, email: str, password: str) -> str:
    """Authenticate a user and set a new session cookie."""
    user = authenticate_user(db, email, password)
    token = create_session(db, user.id)
    db.commit()

    return token