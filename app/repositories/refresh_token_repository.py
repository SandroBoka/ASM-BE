from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db
            .query(RefreshToken)
            .filter(RefreshToken.TokenHash == token_hash)  # type: ignore[arg-type]
            .first()
        )

    def update_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def revoke_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.Opozvan = True
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def revoke_all_for_person(self, person_id: int) -> None:
        (
            self.db
            .query(RefreshToken)
            .filter(RefreshToken.IdOsobe == person_id)  # type: ignore[arg-type]
            .update({"Opozvan": True})
        )

        self.db.commit()
