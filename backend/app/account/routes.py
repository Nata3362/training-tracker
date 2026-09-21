"""HTTP routes for account registration and session lifecycle actions.

This module owns the account-facing workflow and keeps cookie handling at the
HTTP boundary.
"""

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session as DBSession

from ..authentication.auth import (
    authenticate_user,
    create_session,
    revoke_session,
)
from ..person.schemas import LoginBody, SignupBody
from ..database import get_db
from ..schemas import OkResponse
from .service import register_account, login_user

router = APIRouter(prefix="/account",tags=["account"])


@router.post("/signup", response_model=OkResponse)
def signup_endpoint(
    payload: SignupBody,
    response: Response,
    db: DBSession = Depends(get_db)
) -> OkResponse:
    """Register a user and person, then set the new session cookie."""
    token = register_account(
        db = db,
        email = payload.email,
        password = payload.password,
        name = payload.name,
    )

    response.set_cookie(
        "session",
        token,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return OkResponse()


@router.post("/login", response_model=OkResponse)
def login_endpoint(
    payload: LoginBody, response: Response, db: DBSession = Depends(get_db)
) -> OkResponse:
    token = login_user(db, payload.email, payload.password)

    response.set_cookie(
        "session",
        token,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return OkResponse()


@router.post("/logout", response_model=OkResponse)
def logout_endpoint(
    response: Response,
    session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> OkResponse:
    """Revoke the current session and clear the session cookie."""
    if session:
        revoke_session(db, session)

    response.delete_cookie("session")

    return OkResponse()