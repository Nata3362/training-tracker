from fastapi import APIRouter, Depends
from .service import get_person
from .models import Person
from .schemas import PersonResponse

router = APIRouter(prefix="/person", tags=["person"])

@router.get("/me", response_model=PersonResponse)
def get_me(person: Person = Depends(get_person)) -> PersonResponse:
    """Return the profile belonging to the authenticated user."""
    return person
