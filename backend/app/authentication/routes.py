"""HTTP routes for reporting and managing authentication state."""

from fastapi import APIRouter, Depends

from .auth import get_user
from .models import User
from .schemas import UserResponse

router = APIRouter(tags=["auth"])


@router.get("/user", response_model=UserResponse)
def user_endpoint(user: User = Depends(get_user)) -> UserResponse:
    """Return the authenticated user's public account identity."""
    return user


# Future authentication operations may include password and session management:
# POST /auth/change-password
# GET  /auth/sessions
# DELETE /auth/sessions/{id}