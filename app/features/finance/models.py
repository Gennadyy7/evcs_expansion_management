from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.models import ChargingStation, Site
from app.features.finance.constants import CostKind, RevenueEntryType, RevisionStatus
from app.features.pm.models import Contract, Project


class BudgetRevision(TimestampMixin, Base):
    __tablename__ = 'budget_revision'
    __table_args__ = (
        UniqueConstraint(
            'project_id',
            'revision_no',
            name='uq_budget_revision_project_no',
        ),
        CheckConstraint(
            'revision_no > 0',
            name='revision_no_positive',
        ),
        CheckConstraint(
            f'revision_status IN ({",".join(repr(s.value) for s in RevisionStatus)})',
            name='status_valid',
        ),
        Index('ix_budget_revision_project', 'project_id'),
        Index('ix_budget_revision_status', 'revision_status'),
        {'schema': 'finance'},
    )

    budget_revision_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique budget revision identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    revision_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='Sequential revision number within the project (1, 2, ...)',
    )
    revision_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=RevisionStatus.DRAFT,
        comment=f'Revision status: {", ".join(s.value for s in RevisionStatus)}',
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when the revision was approved',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='budget_revisions',
        lazy='selectin',
    )
    capex_budget_lines: Mapped[list[CapexBudget]] = relationship(
        'CapexBudget',
        back_populates='budget_revision',
        lazy='raise',
        cascade='all',
        passive_deletes=True,
        order_by='CapexBudget.period_month',
    )

    def __repr__(self) -> str:
        return (
            f'BudgetRevision(project={self.project_id}, '
            f"no={self.revision_no}, status='{self.revision_status}')"
        )

    @property
    def is_approved(self) -> bool:
        return self.revision_status == RevisionStatus.APPROVED


class CapexBudget(TimestampMixin, Base):
    __tablename__ = 'capex_budget'
    __table_args__ = (
        ForeignKeyConstraint(
            ['category_id', 'cost_kind'],
            ['ref.cost_category.category_id', 'ref.cost_category.cost_kind'],
            ondelete='RESTRICT',
            name='fk_capex_budget_category_kind',
        ),
        UniqueConstraint(
            'budget_revision_id',
            'category_id',
            'period_month',
            name='uq_capex_budget_rev_cat_month',
        ),
        CheckConstraint(
            "cost_kind = 'CAPEX'",
            name='kind_capex',
        ),
        CheckConstraint(
            'EXTRACT(DAY FROM period_month) = 1',
            name='period_first_day',
        ),
        CheckConstraint(
            'budget_amount_byn >= 0',
            name='amount_non_negative',
        ),
        Index('ix_capex_budget_revision', 'budget_revision_id'),
        Index('ix_capex_budget_period', 'period_month'),
        {'schema': 'finance'},
    )

    capex_budget_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique CAPEX budget line identifier',
    )
    budget_revision_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('finance.budget_revision.budget_revision_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the budget revision',
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Reference to ref.cost_category (CAPEX only)',
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=CostKind.CAPEX,
        comment='Cost kind discriminator (always CAPEX here)',
    )
    period_month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Planning month (first day of month)',
    )
    budget_amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Planned CAPEX amount in BYN',
    )

    budget_revision: Mapped[BudgetRevision] = relationship(
        'BudgetRevision',
        back_populates='capex_budget_lines',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'CapexBudget(revision={self.budget_revision_id}, '
            f'cat={self.category_id}, month={self.period_month})'
        )


class CapexCommitment(TimestampMixin, Base):
    __tablename__ = 'capex_commitment'
    __table_args__ = (
        ForeignKeyConstraint(
            ['category_id', 'cost_kind'],
            ['ref.cost_category.category_id', 'ref.cost_category.cost_kind'],
            ondelete='RESTRICT',
            name='fk_capex_commitment_category_kind',
        ),
        UniqueConstraint('erp_line_id', name='uq_capex_commitment_erp_line'),
        CheckConstraint(
            "cost_kind = 'CAPEX'",
            name='kind_capex',
        ),
        CheckConstraint(
            'amount_byn <> 0',
            name='amount_non_zero',
        ),
        Index('ix_capex_commitment_project', 'project_id'),
        Index('ix_capex_commitment_contract', 'contract_id'),
        {'schema': 'finance'},
    )

    commitment_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique CAPEX commitment identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    contract_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.contract.contract_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the signed contract',
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Reference to ref.cost_category (CAPEX only)',
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=CostKind.CAPEX,
        comment='Cost kind discriminator (always CAPEX here)',
    )
    commitment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Date when the commitment was created',
    )
    amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Committed amount in BYN (non-zero, sign indicates direction)',
    )
    erp_line_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Source line identifier in ERP for idempotency',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='capex_commitments',
        lazy='selectin',
    )
    contract: Mapped[Contract | None] = relationship(
        'Contract',
        back_populates='capex_commitments',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f'CapexCommitment(project={self.project_id}, amount={self.amount_byn})'


class CapexActual(TimestampMixin, Base):
    __tablename__ = 'capex_actual'
    __table_args__ = (
        ForeignKeyConstraint(
            ['category_id', 'cost_kind'],
            ['ref.cost_category.category_id', 'ref.cost_category.cost_kind'],
            ondelete='RESTRICT',
            name='fk_capex_actual_category_kind',
        ),
        UniqueConstraint(
            'source_system_id',
            'source_line_id',
            name='uq_capex_actual_source_line',
        ),
        CheckConstraint(
            "cost_kind = 'CAPEX'",
            name='kind_capex',
        ),
        CheckConstraint(
            'amount_byn <> 0',
            name='amount_non_zero',
        ),
        Index('ix_capex_actual_project_date', 'project_id', 'posted_on'),
        {'schema': 'finance'},
    )

    capex_actual_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique CAPEX actual fact identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    station_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='SET NULL'),
        nullable=True,
        comment='Direct station attribution (NULL = site-level, needs allocation)',
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Reference to ref.cost_category (CAPEX only)',
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=CostKind.CAPEX,
        comment='Cost kind discriminator (always CAPEX here)',
    )
    posted_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Posting date',
    )
    amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Actual amount in BYN (non-zero, sign indicates direction)',
    )
    source_system_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('integration.source_system.source_system_id', ondelete='SET NULL'),
        nullable=True,
        comment='Source system that originated this fact',
    )
    source_document_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Source document identifier',
    )
    source_line_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Source line identifier for idempotency',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='capex_actuals',
        lazy='selectin',
    )
    station: Mapped[ChargingStation | None] = relationship(
        'ChargingStation',
        back_populates='capex_actuals',
        lazy='selectin',
    )
    allocations: Mapped[list[CapexAllocation]] = relationship(
        'CapexAllocation',
        back_populates='capex_actual',
        lazy='raise',
        cascade='all',
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f'CapexActual(project={self.project_id}, '
            f'amount={self.amount_byn}, posted={self.posted_on})'
        )

    @property
    def is_site_level(self) -> bool:
        return self.station_id is None


class CapexAllocation(TimestampMixin, Base):
    __tablename__ = 'capex_allocation'
    __table_args__ = (
        CheckConstraint(
            'allocated_amount_byn <> 0',
            name='amount_non_zero',
        ),
        {'schema': 'finance'},
    )

    capex_actual_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('finance.capex_actual.capex_actual_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the CAPEX actual fact',
    )
    station_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the station receiving the allocation',
    )
    allocated_amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Allocated amount in BYN',
    )
    method: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Allocation method description',
    )

    capex_actual: Mapped[CapexActual] = relationship(
        'CapexActual',
        back_populates='allocations',
        lazy='selectin',
    )
    station: Mapped[ChargingStation] = relationship(
        'ChargingStation',
        back_populates='capex_allocations',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'CapexAllocation(actual={self.capex_actual_id}, '
            f'station={self.station_id}, amount={self.allocated_amount_byn})'
        )


class CapexPayment(TimestampMixin, Base):
    __tablename__ = 'capex_payment'
    __table_args__ = (
        UniqueConstraint('erp_payment_id', name='uq_capex_payment_erp_id'),
        CheckConstraint(
            'amount_byn <> 0',
            name='amount_non_zero',
        ),
        Index('ix_capex_payment_project', 'project_id'),
        Index('ix_capex_payment_contract', 'contract_id'),
        {'schema': 'finance'},
    )

    capex_payment_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique CAPEX payment identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    contract_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.contract.contract_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the contract being paid',
    )
    paid_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Payment date',
    )
    amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Paid amount in BYN (non-zero)',
    )
    erp_payment_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Payment identifier in ERP for idempotency',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='capex_payments',
        lazy='selectin',
    )
    contract: Mapped[Contract | None] = relationship(
        'Contract',
        back_populates='capex_payments',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'CapexPayment(project={self.project_id}, '
            f'amount={self.amount_byn}, paid={self.paid_on})'
        )


class CapexForecastEac(TimestampMixin, Base):
    __tablename__ = 'capex_forecast_eac'
    __table_args__ = (
        ForeignKeyConstraint(
            ['category_id', 'cost_kind'],
            ['ref.cost_category.category_id', 'ref.cost_category.cost_kind'],
            ondelete='RESTRICT',
            name='fk_capex_forecast_eac_category_kind',
        ),
        UniqueConstraint(
            'project_id',
            'category_id',
            'as_of_date',
            name='uq_capex_forecast_eac_project_cat_date',
        ),
        CheckConstraint(
            "cost_kind = 'CAPEX'",
            name='kind_capex',
        ),
        CheckConstraint(
            'eac_total_byn >= 0',
            name='non_negative',
        ),
        Index('ix_capex_forecast_eac_project', 'project_id'),
        {'schema': 'finance'},
    )

    eac_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique EAC forecast identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Reference to ref.cost_category (CAPEX only)',
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=CostKind.CAPEX,
        comment='Cost kind discriminator (always CAPEX here)',
    )
    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Forecast snapshot date',
    )
    eac_total_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Estimated total cost at completion (already includes actuals)',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='capex_forecasts',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'CapexForecastEac(project={self.project_id}, '
            f'eac={self.eac_total_byn}, as_of={self.as_of_date})'
        )


class OpexEntry(TimestampMixin, Base):
    __tablename__ = 'opex_entry'
    __table_args__ = (
        ForeignKeyConstraint(
            ['category_id', 'cost_kind'],
            ['ref.cost_category.category_id', 'ref.cost_category.cost_kind'],
            ondelete='RESTRICT',
            name='fk_opex_entry_category_kind',
        ),
        UniqueConstraint(
            'source_system_id',
            'source_line_id',
            name='uq_opex_entry_source_line',
        ),
        CheckConstraint(
            "cost_kind = 'OPEX'",
            name='kind_opex',
        ),
        CheckConstraint(
            'amount_byn <> 0',
            name='amount_non_zero',
        ),
        Index('ix_opex_site_date', 'site_id', 'posted_on'),
        {'schema': 'finance'},
    )

    opex_entry_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique OPEX entry identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the site',
    )
    station_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='SET NULL'),
        nullable=True,
        comment='Direct station attribution (NULL = site-level, needs allocation)',
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Reference to ref.cost_category (OPEX only)',
    )
    cost_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=CostKind.OPEX,
        comment='Cost kind discriminator (always OPEX here)',
    )
    posted_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Posting date',
    )
    amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='OPEX amount in BYN (non-zero, sign indicates direction)',
    )
    source_system_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('integration.source_system.source_system_id', ondelete='SET NULL'),
        nullable=True,
        comment='Source system that originated this entry',
    )
    source_line_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Source line identifier for idempotency',
    )

    site: Mapped[Site] = relationship(
        'Site',
        back_populates='opex_entries',
        lazy='selectin',
    )
    station: Mapped[ChargingStation | None] = relationship(
        'ChargingStation',
        back_populates='opex_entries',
        lazy='selectin',
    )
    allocations: Mapped[list[OpexAllocation]] = relationship(
        'OpexAllocation',
        back_populates='opex_entry',
        lazy='raise',
        cascade='all',
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f'OpexEntry(site={self.site_id}, '
            f'amount={self.amount_byn}, posted={self.posted_on})'
        )

    @property
    def is_site_level(self) -> bool:
        return self.station_id is None


class OpexAllocation(TimestampMixin, Base):
    __tablename__ = 'opex_allocation'
    __table_args__ = (
        CheckConstraint(
            'allocated_amount_byn <> 0',
            name='amount_non_zero',
        ),
        {'schema': 'finance'},
    )

    opex_entry_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('finance.opex_entry.opex_entry_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the OPEX entry',
    )
    station_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the station receiving the allocation',
    )
    allocated_amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Allocated amount in BYN',
    )
    method: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Allocation method description',
    )

    opex_entry: Mapped[OpexEntry] = relationship(
        'OpexEntry',
        back_populates='allocations',
        lazy='selectin',
    )
    station: Mapped[ChargingStation] = relationship(
        'ChargingStation',
        back_populates='opex_allocations',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'OpexAllocation(entry={self.opex_entry_id}, '
            f'station={self.station_id}, amount={self.allocated_amount_byn})'
        )


class RevenueEntry(TimestampMixin, Base):
    __tablename__ = 'revenue_entry'
    __table_args__ = (
        UniqueConstraint(
            'source_system_id',
            'source_line_id',
            name='uq_revenue_entry_source_line',
        ),
        CheckConstraint(
            'net_revenue_byn <> 0',
            name='amount_non_zero',
        ),
        CheckConstraint(
            f'entry_type IN ({",".join(repr(t.value) for t in RevenueEntryType)})',
            name='type_valid',
        ),
        Index('ix_revenue_site_date', 'site_id', 'recognized_on'),
        {'schema': 'finance'},
    )

    revenue_entry_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique revenue entry identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the site',
    )
    station_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='SET NULL'),
        nullable=True,
        comment='Direct station attribution (NULL = site-level, needs allocation)',
    )
    recognized_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Revenue recognition date',
    )
    net_revenue_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Net revenue in BYN, without VAT (non-zero)',
    )
    source_system_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('integration.source_system.source_system_id', ondelete='SET NULL'),
        nullable=True,
        comment='Source system that originated this entry',
    )
    source_line_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Source line identifier for idempotency',
    )
    entry_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=RevenueEntryType.CHARGE,
        comment=f'Entry type: {", ".join(t.value for t in RevenueEntryType)}',
    )

    site: Mapped[Site] = relationship(
        'Site',
        back_populates='revenue_entries',
        lazy='selectin',
    )
    station: Mapped[ChargingStation | None] = relationship(
        'ChargingStation',
        back_populates='revenue_entries',
        lazy='selectin',
    )
    allocations: Mapped[list[RevenueAllocation]] = relationship(
        'RevenueAllocation',
        back_populates='revenue_entry',
        lazy='raise',
        cascade='all',
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f'RevenueEntry(site={self.site_id}, '
            f'revenue={self.net_revenue_byn}, recognized={self.recognized_on})'
        )

    @property
    def is_site_level(self) -> bool:
        return self.station_id is None


class RevenueAllocation(TimestampMixin, Base):
    __tablename__ = 'revenue_allocation'
    __table_args__ = (
        CheckConstraint(
            'allocated_amount_byn <> 0',
            name='amount_non_zero',
        ),
        {'schema': 'finance'},
    )

    revenue_entry_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('finance.revenue_entry.revenue_entry_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the revenue entry',
    )
    station_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the station receiving the allocation',
    )
    allocated_amount_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment='Allocated amount in BYN',
    )
    method: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Allocation method description',
    )

    revenue_entry: Mapped[RevenueEntry] = relationship(
        'RevenueEntry',
        back_populates='allocations',
        lazy='selectin',
    )
    station: Mapped[ChargingStation] = relationship(
        'ChargingStation',
        back_populates='revenue_allocations',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'RevenueAllocation(entry={self.revenue_entry_id}, '
            f'station={self.station_id}, amount={self.allocated_amount_byn})'
        )
