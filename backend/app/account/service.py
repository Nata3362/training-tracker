# Create User and Person 
from sqlalchemy.orm import Session
from ..authentication.auth import create_session, create_user
from ..person.service import create_person

def register_account(
        db: Session,
        email: str,
        password: str,
        name: str, 
) -> str:
    user = create_user(db ,email, password, name)
    person = create_person(db, user.id, name)
    token = create_session(db, user.id)
    db.commit()

    return token