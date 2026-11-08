from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.models import Program, Site
from app.features.pm.constants import (
    ApprovalStatus,
    PlanScenario,
    ProjectStatus,
    ProjectType,
)


class Project(TimestampMixin, Base):
    __tablename__ = 'project'
    __table_args__ = (
        UniqueConstraint('project_code', name='uq_project_code'),
        CheckConstraint(
            f'project_type IN ({",".join(repr(t.value) for t in ProjectType)})',
            name='ck_project_type_valid',
        ),
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in ProjectStatus)})',
            name='ck_project_status_valid',
        ),
        CheckConstraint(
            'baseline_finish IS NULL OR baseline_start IS NULL OR baseline_finish >= baseline_start',
            name='ck_project_baseline_valid',
        ),
        Index('ix_project_site', 'site_id'),
        Index('ix_project_status', 'status'),
        {'schema': 'pm'},
    )

    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique project identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.site.site_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the site being developed',
    )
    project_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Unique project code (e.g., "PRJ-2024-001")',
    )
    project_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=ProjectType.NEW_BUILD,
        comment=f'Project type: {", ".join(t.value for t in ProjectType)}',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Project name in Russian',
    )
    project_manager_user_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='IAM user ID of the project manager',
    )
    baseline_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Baseline planned start date',
    )
    baseline_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Baseline planned finish date',
    )
    forecast_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Current forecasted finish date (for delay tracking)',
    )
    actual_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual finish date',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=ProjectStatus.PLANNED,
        comment=f'Project status: {", ".join(s.value for s in ProjectStatus)}',
    )

    site: Mapped[Site] = relationship(
        'Site',
        back_populates='projects',
        lazy='selectin',
    )
    # stages: Mapped[list[StageExecution]] = relationship(
    #     'StageExecution',
    #     back_populates='project',
    #     lazy='selectin',
    #     cascade='all, delete-orphan',
    #     order_by='StageExecution.stage_no',
    # )
    # scopes: Mapped[list[ProjectScope]] = relationship(
    #     'ProjectScope',
    #     back_populates='project',
    #     lazy='selectin',
    #     cascade='all, delete-orphan',
    # )
    # documents: Mapped[list[ProjectDocument]] = relationship(
    #     'ProjectDocument',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # permits: Mapped[list[Permit]] = relationship(
    #     'Permit',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # contracts: Mapped[list[Contract]] = relationship(
    #     'Contract',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # purchase_orders: Mapped[list[PurchaseOrder]] = relationship(
    #     'PurchaseOrder',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # construction_works: Mapped[list[ConstructionWork]] = relationship(
    #     'ConstructionWork',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # commissioning_tests: Mapped[list[CommissioningTest]] = relationship(
    #     'CommissioningTest',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )
    # issues: Mapped[list[Issue]] = relationship(
    #     'Issue',
    #     back_populates='project',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )

    def __repr__(self) -> str:
        return f"Project(code='{self.project_code}', status='{self.status}')"

    @property
    def is_active(self) -> bool:
        return self.status in (ProjectStatus.ACTIVE, ProjectStatus.BLOCKED)

    @property
    def is_completed(self) -> bool:
        return self.status == ProjectStatus.COMPLETED

    @property
    def forecast_delay_days(self) -> int | None:
        if self.forecast_finish and self.baseline_finish:
            return (self.forecast_finish - self.baseline_finish).days
        return None


class NetworkPlan(TimestampMixin, Base):
    __tablename__ = 'network_plan'
    __table_args__ = (
        UniqueConstraint(
            'program_id',
            'plan_version',
            'scenario',
            name='uq_network_plan_program_version_scenario',
        ),
        CheckConstraint(
            f'approval_status IN ({",".join(repr(s.value) for s in ApprovalStatus)})',
            name='ck_network_plan_approval_status_valid',
        ),
        CheckConstraint(
            f'scenario IN ({",".join(repr(s.value) for s in PlanScenario)})',
            name='ck_network_plan_scenario_valid',
        ),
        Index('ix_network_plan_program', 'program_id'),
        {'schema': 'pm'},
    )

    network_plan_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique network plan identifier',
    )
    program_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.program.program_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the development program',
    )
    plan_version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Plan version (e.g., "v1.0", "v2.1")',
    )
    scenario: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=PlanScenario.BASE,
        comment=f'Plan scenario: {", ".join(s.value for s in PlanScenario)}',
    )
    approval_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=ApprovalStatus.DRAFT,
        comment=f'Approval status: {", ".join(s.value for s in ApprovalStatus)}',
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Approval timestamp',
    )

    program: Mapped[Program] = relationship(
        'Program',
        back_populates='network_plans',
        lazy='selectin',
    )
    # lines: Mapped[list[NetworkPlanLine]] = relationship(
    #     'NetworkPlanLine',
    #     back_populates='network_plan',
    #     lazy='raise',
    #     cascade='all, delete-orphan',
    # )

    def __repr__(self) -> str:
        return (
            f"NetworkPlan(version='{self.plan_version}', "
            f"scenario='{self.scenario}', status='{self.approval_status}')"
        )

    @property
    def is_approved(self) -> bool:
        return self.approval_status == ApprovalStatus.APPROVED
