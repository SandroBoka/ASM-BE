import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.person import Person
from app.models.refresh_token import RefreshToken
from app.repositories.person_repository import PersonRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas import AuthTokenResponse, AuthUserResponse
from app.services.person_service import PersonService


class AuthService:
    def __init__(
            self,
            person_repository: PersonRepository,
            refresh_token_repository: RefreshTokenRepository
    ):
        self.person_repository = person_repository
        self.refresh_token_repository = refresh_token_repository

    def login(self, email: str, password: str) -> AuthTokenResponse:
        person = self.person_repository.get_person_by_email(email.strip())

        if person is None or not PersonService.verify_password(password, person.Lozinka):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neispravan email ili lozinka"
            )

        return self._create_auth_response(person)

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        token_hash = self._hash_refresh_token(refresh_token)
        stored_token = self.refresh_token_repository.get_refresh_token_by_hash(token_hash)

        if stored_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neispravan refresh token"
            )

        if stored_token.Opozvan:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token je opozvan"
            )

        if stored_token.IstekaoU < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token je istekao"
            )

        person = self.person_repository.get_person_by_id(stored_token.IdOsobe)

        if person is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Korisnik više ne postoji"
            )

        stored_token.Opozvan = True
        self.refresh_token_repository.update_refresh_token(stored_token)

        return self._create_auth_response(person)

    def logout(self, refresh_token: str) -> None:
        token_hash = self._hash_refresh_token(refresh_token)
        stored_token = self.refresh_token_repository.get_refresh_token_by_hash(token_hash)

        if stored_token is not None:
            self.refresh_token_repository.revoke_refresh_token(stored_token)

    def _create_auth_response(self, person: Person) -> AuthTokenResponse:
        user = self.build_user_response(person)
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(person.IdOsobe)

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user
        )

    @staticmethod
    def build_user_response(person: Person) -> AuthUserResponse:
        if person.employee_profile is not None:
            return AuthUserResponse(
                IdOsobe=person.IdOsobe,
                Ime=person.Ime,
                Prezime=person.Prezime,
                Email=person.Email,
                TipKorisnika="employee",
                Uloga=person.employee_profile.Uloga
            )

        if person.customer_profile is not None:
            return AuthUserResponse(
                IdOsobe=person.IdOsobe,
                Ime=person.Ime,
                Prezime=person.Prezime,
                Email=person.Email,
                TipKorisnika="customer",
                Uloga=None
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Osoba nema dodijeljenu korisničku ulogu"
        )

    @staticmethod
    def _create_access_token(user: AuthUserResponse) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

        payload = {
            "sub": str(user.IdOsobe),
            "email": str(user.Email),
            "type": user.TipKorisnika,
            "role": user.Uloga,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp())
        }

        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )

    def _create_refresh_token(self, person_id: int) -> str:
        plain_token = secrets.token_urlsafe(64)
        token_hash = self._hash_refresh_token(plain_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

        refresh_token = RefreshToken(
            IdOsobe=person_id,
            TokenHash=token_hash,
            IstekaoU=expires_at,
            Opozvan=False
        )

        self.refresh_token_repository.create_refresh_token(refresh_token)

        return plain_token

    @staticmethod
    def _hash_refresh_token(refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
