from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---- Requests ----

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    provider: str = "EMAIL_PASSWORD"
    email: EmailStr | None = None
    password: str | None = None
    id_token: str | None = None  # for social login


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    city: str | None = None
    country: str | None = None


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ConfirmPasswordResetRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# ---- Responses ----

class UserResponse(BaseModel):
    id: str
    email: str
    status: str
    created_at: datetime


class ProfileResponse(BaseModel):
    user_id: str
    first_name: str | None
    last_name: str | None
    city: str | None
    country: str | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ErrorResponse(BaseModel):
    detail: str
