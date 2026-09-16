"""HTTP routes for reporting and managing authentication state."""

import uuid

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session as DBSession

from .auth import require_auth
from .models import User
from ..database import get_db

router = APIRouter(tags=["auth"])


@router.get("/user")
def user_endpoint(user_id: uuid.UUID = Depends(require_auth), db: DBSession = Depends(get_db)):
    """Return the authenticated user's public account identity."""
    user = db.get(User, user_id)
    return {"id": user.id, "email": user.email, "name": user.name}


# Future authentication operations may include password and session management:
# POST /auth/refresh
# POST /auth/change-password
# GET  /auth/sessions
# DELETE /auth/sessions/{id}