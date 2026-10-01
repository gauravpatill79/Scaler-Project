from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_auth_service, get_password_reset_service, get_user_service
from app.api.schemas import (
    ConfirmPasswordResetRequest,
    LoginRequest,
    ProfileResponse,
    RegisterRequest,
    RequestPasswordResetRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.domain.enums import AuthProviderType
from app.domain.exceptions import DomainError
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: RegisterRequest, service: UserService = Depends(get_user_service)):
    try:
        user = service.register(req.email, req.password, req.first_name or "", req.last_name or "")
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return UserResponse(id=user.id, email=user.email, status=user.status.value, created_at=user.created_at)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, service: AuthService = Depends(get_auth_service)):
    credentials = req.model_dump(exclude_none=True)
    try:
        provider_type = AuthProviderType(req.provider)
        token = service.login(provider_type, credentials)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.get("/{user_id}/profile", response_model=ProfileResponse)
def get_profile(user_id: str, service: UserService = Depends(get_user_service)):
    try:
        profile = service.get_profile(user_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return ProfileResponse(
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        city=profile.city,
        country=profile.country,
    )


@router.patch("/{user_id}/profile", response_model=ProfileResponse)
def update_profile(user_id: str, req: UpdateProfileRequest, service: UserService = Depends(get_user_service)):
    try:
        profile = service.update_profile(user_id, **req.model_dump(exclude_none=True))
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return ProfileResponse(
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        city=profile.city,
        country=profile.country,
    )


@router.post("/password-reset/request", status_code=202)
def request_password_reset(
    req: RequestPasswordResetRequest, service: PasswordResetService = Depends(get_password_reset_service)
):
    service.request_reset(req.email)
    # Always 202, regardless of whether the email exists — avoids user enumeration.
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=200)
def confirm_password_reset(
    req: ConfirmPasswordResetRequest, service: PasswordResetService = Depends(get_password_reset_service)
):
    try:
        service.confirm_reset(req.token, req.new_password)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
    return {"detail": "Password updated successfully."}
