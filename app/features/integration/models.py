"""Integration feature models.

TEMPORARY / WORK-IN-PROGRESS
=============================
This module currently contains ONLY the minimal schema required to satisfy
foreign-key dependencies from the finance feature (source_system_id columns
in capex_actual, opex_entry, revenue_entry).

The full integration feature — external_identity mapping, ingestion_batch
tracking, inbox_event queue, and the surrounding ETL contracts — has NOT
been designed or implemented yet. This file is a placeholder and will be
significantly reworked in a future development phase. Do not build any
business logic on top of it beyond the FK reference.
"""

from uuid import UUID, uuid4

from sqlalchemy import Boolean, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class SourceSystem(TimestampMixin, Base):
    """Minimal source-system registry.

    NOTE: Placeholder implementation. Only the columns needed for the FK
    reference from finance are present. The richer integration surface
    (identity mapping, ingestion tracking, event inbox) is planned for a
    later phase and may change this model.
    """

    __tablename__ = 'source_system'
    __table_args__ = (
        UniqueConstraint('code', name='uq_source_system_code'),
        {'schema': 'integration'},
    )

    source_system_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique source system identifier',
    )
    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='System code (e.g., CPMS, ERP, BILLING)',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='System name in Russian',
    )
    system_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='System kind classification',
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default='true',
        comment='Whether the source system is currently active',
    )

    def __repr__(self) -> str:
        return f"SourceSystem(code='{self.code}', active={self.is_active})"
