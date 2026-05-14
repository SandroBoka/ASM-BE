"""create refresh token table

Revision ID: 280cf4017360
Revises: 095d3dce8249
Create Date: 2026-05-14 10:27:30.722622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '280cf4017360'
down_revision: Union[str, Sequence[str], None] = '095d3dce8249'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_token",
        sa.Column("IdRefreshTokena", sa.Integer(), nullable=False),
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.Column("TokenHash", sa.String(length=255), nullable=False),
        sa.Column("IstekaoU", sa.DateTime(timezone=True), nullable=False),
        sa.Column("Opozvan", sa.Boolean(), nullable=False),
        sa.Column("StvorenU", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["IdOsobe"],
            ["osoba.IdOsobe"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("IdRefreshTokena")
    )

    op.create_index(
        op.f("ix_refresh_token_IdRefreshTokena"),
        "refresh_token",
        ["IdRefreshTokena"],
        unique=False
    )

    op.create_index(
        op.f("ix_refresh_token_IdOsobe"),
        "refresh_token",
        ["IdOsobe"],
        unique=False
    )

    op.create_index(
        op.f("ix_refresh_token_TokenHash"),
        "refresh_token",
        ["TokenHash"],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_token_TokenHash"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_IdOsobe"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_IdRefreshTokena"), table_name="refresh_token")
    op.drop_table("refresh_token")
