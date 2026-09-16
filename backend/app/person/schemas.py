"""Pydantic schemas for person profile requests and responses."""

from pydantic import BaseModel, EmailStr


class SignupBody(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str

