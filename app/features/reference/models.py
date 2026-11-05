from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Identity,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Region(TimestampMixin, Base):
    __tablename__ = 'region'
    __table_args__ = {'schema': 'ref'}  # noqa: RUF012

    region_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment="Short region code (e.g., 'MINSK_OBL')",
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Full name in Russian',
    )
    parent_region_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey('ref.region.region_id', ondelete='SET NULL'),
        nullable=True,
        comment='Parent region (for hierarchy)',
    )

    parent: Mapped[Region | None] = relationship(
        'Region',
        remote_side=region_id,
        back_populates='children',
        lazy='selectin',
    )
    children: Mapped[list[Region]] = relationship(
        'Region',
        back_populates='parent',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f"Region(region_id={self.region_id}, code='{self.code}')"


class ChargerType(TimestampMixin, Base):
    __tablename__ = 'charger_type'
    __table_args__ = (
        CheckConstraint(
            "code IN ('AC','HYBRID','DC','OTHER')",
            name='charger_type_code_check',
        ),
        {'schema': 'ref'},
    )

    charger_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        Identity(always=True),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment='Type code: AC, HYBRID, DC, OTHER',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Type name in Russian',
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Type description',
    )

    def __repr__(self) -> str:
        return f"ChargerType(code='{self.code}')"


class ConnectorType(TimestampMixin, Base):
    __tablename__ = 'connector_type'
    __table_args__ = {'schema': 'ref'}  # noqa: RUF012

    connector_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        Identity(always=True),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment='Connector code: TYPE2, CCS2, CHADEMO, etc.',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Connector name in Russian',
    )

    def __repr__(self) -> str:
        return f"ConnectorType(code='{self.code}')"


class SiteType(TimestampMixin, Base):
    __tablename__ = 'site_type'
    __table_args__ = {'schema': 'ref'}  # noqa: RUF012

    site_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        Identity(always=True),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment='Site type code',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Site type name in Russian',
    )

    def __repr__(self) -> str:
        return f"SiteType(code='{self.code}')"


class CostCategory(TimestampMixin, Base):
    __tablename__ = 'cost_category'
    __table_args__ = (
        CheckConstraint(
            "cost_kind IN ('CAPEX','OPEX')",
            name='cost_category_kind_check',
        ),
        UniqueConstraint(
            'cost_kind',
            'code',
            name='uq_cost_category_kind_code',
        ),
        UniqueConstraint(
            'category_id',
            'cost_kind',
            name='uq_cost_category_id_kind',
            comment='Used as composite FK in financial tables',
        ),
        {'schema': 'ref'},
    )

    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        Identity(always=True),
        primary_key=True,
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Cost kind: CAPEX or OPEX',
    )
    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Category code: EVSE, GRID, ENERGY, RENT, etc.',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Category name in Russian',
    )

    def __repr__(self) -> str:
        return f"CostCategory(cost_kind='{self.cost_kind}', code='{self.code}')"

    @property
    def is_capex(self) -> bool:
        return self.cost_kind == 'CAPEX'

    @property
    def is_opex(self) -> bool:
        return self.cost_kind == 'OPEX'


class ProjectStage(TimestampMixin, Base):
    __tablename__ = 'project_stage'
    __table_args__ = (
        CheckConstraint(
            'stage_no BETWEEN 0 AND 13',
            name='project_stage_no_check',
        ),
        {'schema': 'ref'},
    )

    stage_no: Mapped[int] = mapped_column(
        SmallInteger,
        primary_key=True,
        comment='Stage number (0-13), fixed sequence',
    )
    code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment='Stage string code: PROGRAM, SITE, SURVEY, etc.',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Stage name in Russian',
    )
    is_milestone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('true'),
        comment='Whether the stage is a milestone (gate)',
    )

    def __repr__(self) -> str:
        return f"ProjectStage(stage_no={self.stage_no}, code='{self.code}')"
