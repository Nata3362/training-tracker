"""Wires the auth module to the domain (Person) and hosts every auth-adjacent endpoint.

Every app/authentication/ endpoint lives here: signup, login, logout, /user.
signup and /user reach into Person, which is the one deliberate crossing; login and
logout don't touch Person at all but are exposed here anyway, since nothing under
app/authentication/ defines routes.
"""

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from .authentication.auth import (
    authenticate_user,
    create_session,
    create_user,
    require_auth,
    revoke_session,
)
from .authentication.models import User
from .schemas import LoginBody, SignupBody
from .database import get_db
from .models import Person

router = APIRouter(tags=["auth"])


@router.post("/auth/signup")
def signup_endpoint(
    payload: SignupBody, response: Response, db: DBSession = Depends(get_db)
):
    user = create_user(db, payload.email, payload.password)
    db.add(Person(user_id=user.id, name=payload.name))
    db.commit()
    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@router.post("/auth/login")
def login_endpoint(
    payload: LoginBody, response: Response, db: DBSession = Depends(get_db)
):
    # no Person involved — pure authentication.auth, exposed here because
    # nothing under app/authentication/ defines routes
    user = authenticate_user(db, payload.email, payload.password)
    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@router.post("/auth/logout")
def logout_endpoint(
    response: Response,
    session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
):
    if session:
        revoke_session(db, session)
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/user")
def user_endpoint(user_id: int = Depends(require_auth), db: DBSession = Depends(get_db)):
    user = db.get(User, user_id)
    person = db.scalar(select(Person).where(Person.user_id == user_id))
    return {"id": user.id, "email": user.email, "name": person.name}
