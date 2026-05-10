"""create core asm tables

Revision ID: 095d3dce8249
Revises: aa85fd0e271f
Create Date: 2026-05-10 17:59:37.008356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '095d3dce8249'
down_revision: Union[str, Sequence[str], None] = 'aa85fd0e271f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "osoba",
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.Column("Ime", sa.String(length=50), nullable=False),
        sa.Column("Prezime", sa.String(length=50), nullable=False),
        sa.Column("Email", sa.String(length=100), nullable=False),
        sa.Column("Telefon", sa.String(length=30), nullable=True),
        sa.Column("Lozinka", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("IdOsobe"),
        sa.UniqueConstraint("Email")
    )

    op.create_index(
        op.f("ix_osoba_IdOsobe"),
        "osoba",
        ["IdOsobe"],
        unique=False
    )

    op.create_index(
        op.f("ix_osoba_Email"),
        "osoba",
        ["Email"],
        unique=False
    )

    op.create_table(
        "korisnik",
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["IdOsobe"],
            ["osoba.IdOsobe"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("IdOsobe")
    )

    op.create_table(
        "zaposlenik",
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.Column(
            "Uloga",
            sa.String(length=50),
            nullable=False,
            server_default="serviser"
        ),
        sa.ForeignKeyConstraint(
            ["IdOsobe"],
            ["osoba.IdOsobe"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("IdOsobe")
    )

    op.create_table(
        "vozilo",
        sa.Column("IdVozila", sa.Integer(), nullable=False),
        sa.Column("Marka", sa.String(length=50), nullable=False),
        sa.Column("Model", sa.String(length=50), nullable=False),
        sa.Column("Godina", sa.Integer(), nullable=False),
        sa.Column("VrstaMotora", sa.String(length=50), nullable=False),
        sa.Column("RegOznaka", sa.String(length=20), nullable=False),
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            '"Godina" BETWEEN 1900 AND 2100',
            name="chk_vozilo_godina"
        ),
        sa.ForeignKeyConstraint(
            ["IdOsobe"],
            ["korisnik.IdOsobe"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("IdVozila"),
        sa.UniqueConstraint("RegOznaka")
    )

    op.create_index(
        op.f("ix_vozilo_IdVozila"),
        "vozilo",
        ["IdVozila"],
        unique=False
    )

    op.create_index(
        op.f("ix_vozilo_RegOznaka"),
        "vozilo",
        ["RegOznaka"],
        unique=False
    )

    op.create_table(
        "termin",
        sa.Column("IdTermina", sa.Integer(), nullable=False),
        sa.Column("Datum", sa.Date(), nullable=False),
        sa.Column("VrijemeOd", sa.Time(), nullable=False),
        sa.Column("VrijemeDo", sa.Time(), nullable=False),
        sa.Column(
            "Status",
            sa.String(length=20),
            nullable=False,
            server_default="slobodan"
        ),
        sa.CheckConstraint(
            '"Status" IN (\'slobodan\', \'zauzet\', \'otkazan\')',
            name="chk_termin_status"
        ),
        sa.CheckConstraint(
            '"VrijemeDo" > "VrijemeOd"',
            name="chk_termin_vrijeme"
        ),
        sa.PrimaryKeyConstraint("IdTermina"),
        sa.UniqueConstraint(
            "Datum",
            "VrijemeOd",
            "VrijemeDo",
            name="uq_termin"
        )
    )

    op.create_index(
        op.f("ix_termin_IdTermina"),
        "termin",
        ["IdTermina"],
        unique=False
    )

    op.create_table(
        "rezervacija",
        sa.Column("IdRezervacije", sa.Integer(), nullable=False),
        sa.Column(
            "DatumKreiranja",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE")
        ),
        sa.Column(
            "Status",
            sa.String(length=20),
            nullable=False,
            server_default="na cekanju"
        ),
        sa.Column("KilometrazaVozila", sa.Integer(), nullable=False),
        sa.Column("OpisProblema", sa.Text(), nullable=False),
        sa.Column("KomentarZaposlenika", sa.Text(), nullable=True),
        sa.Column("IdOsobe_Korisnik", sa.Integer(), nullable=False),
        sa.Column("IdTermina", sa.Integer(), nullable=False),
        sa.Column("IdVozila", sa.Integer(), nullable=False),
        sa.Column("IdOsobe_Zaposlenik", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            '"Status" IN (\'na cekanju\', \'odobrena\', \'odbijena\', \'otkazana\', \'zavrsena\')',
            name="chk_rezervacija_status"
        ),
        sa.CheckConstraint(
            '"KilometrazaVozila" >= 0',
            name="chk_rezervacija_kilometraza"
        ),
        sa.ForeignKeyConstraint(
            ["IdOsobe_Korisnik"],
            ["korisnik.IdOsobe"]
        ),
        sa.ForeignKeyConstraint(
            ["IdTermina"],
            ["termin.IdTermina"]
        ),
        sa.ForeignKeyConstraint(
            ["IdVozila"],
            ["vozilo.IdVozila"]
        ),
        sa.ForeignKeyConstraint(
            ["IdOsobe_Zaposlenik"],
            ["zaposlenik.IdOsobe"]
        ),
        sa.PrimaryKeyConstraint("IdRezervacije")
    )

    op.create_index(
        op.f("ix_rezervacija_IdRezervacije"),
        "rezervacija",
        ["IdRezervacije"],
        unique=False
    )

    op.create_index(
        "uq_rezervacija_odobrena_po_terminu",
        "rezervacija",
        ["IdTermina"],
        unique=True,
        postgresql_where=sa.text('"Status" = \'odobrena\'')
    )

    op.create_table(
        "promjena_termina",
        sa.Column("IdZahtjevaPromjene", sa.Integer(), nullable=False),
        sa.Column(
            "DatumZahtjeva",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE")
        ),
        sa.Column(
            "Status",
            sa.String(length=20),
            nullable=False,
            server_default="na cekanju"
        ),
        sa.Column("KomentarZaposlenika", sa.Text(), nullable=True),
        sa.Column("IdRezervacije", sa.Integer(), nullable=False),
        sa.Column("IdStarogTermina", sa.Integer(), nullable=False),
        sa.Column("IdNovogTermina", sa.Integer(), nullable=False),
        sa.Column("IdOsobe_Zaposlenik", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            '"Status" IN (\'na cekanju\', \'prihvacen\', \'odbijen\')',
            name="chk_promjena_termina_status"
        ),
        sa.CheckConstraint(
            '"IdStarogTermina" <> "IdNovogTermina"',
            name="chk_promjena_termina_razliciti_termini"
        ),
        sa.ForeignKeyConstraint(
            ["IdRezervacije"],
            ["rezervacija.IdRezervacije"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["IdStarogTermina"],
            ["termin.IdTermina"]
        ),
        sa.ForeignKeyConstraint(
            ["IdNovogTermina"],
            ["termin.IdTermina"]
        ),
        sa.ForeignKeyConstraint(
            ["IdOsobe_Zaposlenik"],
            ["zaposlenik.IdOsobe"]
        ),
        sa.PrimaryKeyConstraint("IdZahtjevaPromjene")
    )

    op.create_index(
        op.f("ix_promjena_termina_IdZahtjevaPromjene"),
        "promjena_termina",
        ["IdZahtjevaPromjene"],
        unique=False
    )

    op.create_table(
        "rezervacija_usluga",
        sa.Column("IdRezervacije", sa.Integer(), nullable=False),
        sa.Column("IdUsluge", sa.Integer(), nullable=False),
        sa.Column(
            "Kolicina",
            sa.Integer(),
            nullable=False,
            server_default="1"
        ),
        sa.CheckConstraint(
            '"Kolicina" > 0',
            name="chk_rezervacija_usluga_kolicina"
        ),
        sa.ForeignKeyConstraint(
            ["IdRezervacije"],
            ["rezervacija.IdRezervacije"],
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["IdUsluge"],
            ["usluga.IdUsluge"]
        ),
        sa.PrimaryKeyConstraint("IdRezervacije", "IdUsluge")
    )

    op.create_table(
        "obavijest",
        sa.Column("IdObavijesti", sa.Integer(), nullable=False),
        sa.Column("Naslov", sa.String(length=200), nullable=False),
        sa.Column("Tekst", sa.Text(), nullable=False),
        sa.Column(
            "DatumSlanja",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "Procitana",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE")
        ),
        sa.Column("IdOsobe", sa.Integer(), nullable=False),
        sa.Column("IdRezervacije", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["IdOsobe"],
            ["korisnik.IdOsobe"]
        ),
        sa.ForeignKeyConstraint(
            ["IdRezervacije"],
            ["rezervacija.IdRezervacije"]
        ),
        sa.PrimaryKeyConstraint("IdObavijesti")
    )

    op.create_index(
        op.f("ix_obavijest_IdObavijesti"),
        "obavijest",
        ["IdObavijesti"],
        unique=False
    )

    op.create_check_constraint(
        "chk_usluga_trajanje",
        "usluga",
        '"Trajanje" > 0'
    )

    op.create_check_constraint(
        "chk_usluga_cijena",
        "usluga",
        '"Cijena" >= 0'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("chk_usluga_cijena", "usluga", type_="check")
    op.drop_constraint("chk_usluga_trajanje", "usluga", type_="check")

    op.drop_index(op.f("ix_obavijest_IdObavijesti"), table_name="obavijest")
    op.drop_table("obavijest")

    op.drop_table("rezervacija_usluga")

    op.drop_index(
        op.f("ix_promjena_termina_IdZahtjevaPromjene"),
        table_name="promjena_termina"
    )
    op.drop_table("promjena_termina")

    op.drop_index(
        "uq_rezervacija_odobrena_po_terminu",
        table_name="rezervacija",
        postgresql_where=sa.text('"Status" = \'odobrena\'')
    )
    op.drop_index(
        op.f("ix_rezervacija_IdRezervacije"),
        table_name="rezervacija"
    )
    op.drop_table("rezervacija")

    op.drop_index(op.f("ix_termin_IdTermina"), table_name="termin")
    op.drop_table("termin")

    op.drop_index(op.f("ix_vozilo_RegOznaka"), table_name="vozilo")
    op.drop_index(op.f("ix_vozilo_IdVozila"), table_name="vozilo")
    op.drop_table("vozilo")

    op.drop_table("zaposlenik")
    op.drop_table("korisnik")

    op.drop_index(op.f("ix_osoba_Email"), table_name="osoba")
    op.drop_index(op.f("ix_osoba_IdOsobe"), table_name="osoba")
    op.drop_table("osoba")
