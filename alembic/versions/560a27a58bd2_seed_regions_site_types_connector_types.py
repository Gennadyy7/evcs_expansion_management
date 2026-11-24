"""seed_regions_site_types_connector_types

Revision ID: 560a27a58bd2
Revises: 8b75cc0efc67
Create Date: 2026-11-24 20:25:27.227932

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '560a27a58bd2'
down_revision: str | Sequence[str] | None = '8b75cc0efc67'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO ref.site_type (code, name_ru) VALUES
        ('CITY', 'Городская площадка'),
        ('HIGHWAY', 'Трасса'),
        ('MALL', 'Торговый центр'),
        ('OFFICE', 'Офис'),
        ('HOTEL', 'Гостиница'),
        ('GOVERNMENT', 'Госучреждение'),
        ('GAS_STATION', 'АЗС'),
        ('PARKING', 'Парковка'),
        ('OTHER', 'Другое')
        ON CONFLICT (code) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO ref.connector_type (code, name_ru) VALUES
        ('TYPE2', 'Type 2 (Mennekes)'),
        ('CCS2', 'CCS Combo 2'),
        ('CHADEMO', 'CHAdeMO'),
        ('GB_T', 'GB/T')
        ON CONFLICT (code) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO ref.region (code, name_ru, parent_region_id)
        VALUES ('BY', 'Республика Беларусь', NULL)
        ON CONFLICT (code) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO ref.region (code, name_ru, parent_region_id)
        SELECT v.code, v.name_ru, parent.region_id
        FROM (VALUES
            ('MINSK_CITY', 'г. Минск'),
            ('BREST_OBL', 'Брестская область'),
            ('VITEBSK_OBL', 'Витебская область'),
            ('GOMEL_OBL', 'Гомельская область'),
            ('GRODNO_OBL', 'Гродненская область'),
            ('MINSK_OBL', 'Минская область'),
            ('MOGILEV_OBL', 'Могилёвская область')
        ) AS v(code, name_ru)
        CROSS JOIN ref.region AS parent
        WHERE parent.code = 'BY'
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DELETE FROM ref.region
        WHERE code IN (
            'MINSK_CITY', 'BREST_OBL', 'VITEBSK_OBL',
            'GOMEL_OBL', 'GRODNO_OBL', 'MINSK_OBL', 'MOGILEV_OBL'
        );
    """)

    op.execute("DELETE FROM ref.region WHERE code = 'BY';")

    op.execute(
        "DELETE FROM ref.connector_type WHERE code IN ('TYPE2', 'CCS2', 'CHADEMO', 'GB_T');"
    )

    op.execute("""
        DELETE FROM ref.site_type
        WHERE code IN (
            'CITY', 'HIGHWAY', 'MALL', 'OFFICE', 'HOTEL',
            'GOVERNMENT', 'GAS_STATION', 'PARKING', 'OTHER'
        );
    """)
