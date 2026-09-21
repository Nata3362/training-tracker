"""Shared response schemas used across feature modules."""

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True
