"""Pydantic schemas for person profile requests and responses."""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class SignupBody(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str

