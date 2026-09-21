from fastapi import APIRouter, Depends
from .service import get_person
from .models import Person

router = APIRouter(prefix="/person", tags=["person"])

@router.get("/me")
def get_me(person: Person = Depends(get_person)):
    """Return the profile belonging to the authenticated user."""
    return person
