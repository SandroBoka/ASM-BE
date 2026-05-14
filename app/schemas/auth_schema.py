from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    Email: EmailStr
    Lozinka: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class AuthUserResponse(BaseModel):
    IdOsobe: int
    Ime: str
    Prezime: str
    Email: EmailStr
    TipKorisnika: str
    Uloga: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserResponse
