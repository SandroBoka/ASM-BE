from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    IdRefreshTokena = Column(Integer, primary_key=True, index=True)

    IdOsobe = Column(
        Integer,
        ForeignKey("osoba.IdOsobe", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    TokenHash = Column(String(255), nullable=False, unique=True, index=True)

    IstekaoU = Column(DateTime(timezone=True), nullable=False)

    Opozvan = Column(Boolean, nullable=False, default=False)

    StvorenU = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    person = relationship("Person")
