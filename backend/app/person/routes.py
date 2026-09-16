from fastapi import APIRouter, Depends
from .dependencies import require_person
from .models import Person

router = APIRouter(prefix="/person", tags=["person"])

@router.get("/me")
def get_person(person: Person = Depends(require_person)):
    """Return the profile belonging to the authenticated user."""
    return person
