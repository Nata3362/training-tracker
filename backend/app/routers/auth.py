from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_session, revoke_session
from ..database import get_db
from ..models import Person, User
from ..schemas import LoginBody, SignupBody
from ..security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(payload: SignupBody, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(409, "Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()

    db.add(Person(user_id=user.id, name=payload.name))
    db.commit()

    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@router.post("/login")
def login(payload: LoginBody, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@router.post("/logout")
def logout(
    response: Response,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if session:
        revoke_session(db, session)
    response.delete_cookie("session")
    return {"ok": True}
