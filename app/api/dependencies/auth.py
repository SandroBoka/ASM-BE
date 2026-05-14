import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.repositories.person_repository import PersonRepository
from app.schemas import AuthUserResponse
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
) -> AuthUserResponse:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token je istekao"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravan access token"
        )

    person_id = payload.get("sub")

    if person_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token nema korisnički identitet"
        )

    person_repository = PersonRepository(db)
    person = person_repository.get_person_by_id(int(person_id))

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Korisnik više ne postoji"
        )

    return AuthService.build_user_response(person)


def require_customer(
        current_user: AuthUserResponse = Depends(get_current_user)
) -> AuthUserResponse:
    if current_user.TipKorisnika != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pristup je dozvoljen samo korisnicima"
        )

    return current_user


def require_employee(
        current_user: AuthUserResponse = Depends(get_current_user)
) -> AuthUserResponse:
    if current_user.TipKorisnika != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pristup je dozvoljen samo zaposlenicima"
        )

    return current_user


def require_role(*allowed_roles: str):
    def role_checker(
            current_user: AuthUserResponse = Depends(require_employee)
    ) -> AuthUserResponse:
        if current_user.Uloga not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nemate ovlasti za ovu akciju"
            )

        return current_user

    return role_checker
