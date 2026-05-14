from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.repositories.person_repository import PersonRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas import (
    AuthTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    AuthUserResponse
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    person_repository = PersonRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    return AuthService(person_repository, refresh_token_repository)


@router.post("/login", response_model=AuthTokenResponse)
def login(
        request: LoginRequest,
        service: AuthService = Depends(get_auth_service)
):
    return service.login(
        email=str(request.Email),
        password=request.Lozinka
    )


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh(
        request: RefreshTokenRequest,
        service: AuthService = Depends(get_auth_service)
):
    return service.refresh(refresh_token=request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
        request: LogoutRequest,
        service: AuthService = Depends(get_auth_service)
):
    return service.logout(refresh_token=request.refresh_token)


@router.get("/me", response_model=AuthUserResponse)
def me(current_user: AuthUserResponse = Depends(get_current_user)):
    return current_user
