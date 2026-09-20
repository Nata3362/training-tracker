"""HTTP routes for reporting and managing authentication state."""

from fastapi import APIRouter, Depends

from .auth import get_user
from .models import User

router = APIRouter(tags=["auth"])


@router.get("/user")
def user_endpoint(user: User = Depends(get_user())):
    """Return the authenticated user's public account identity."""
    return {"id": user.id, "email": user.email}


# Future authentication operations may include password and session management:
# POST /auth/change-password
# GET  /auth/sessions
# DELETE /auth/sessions/{id}