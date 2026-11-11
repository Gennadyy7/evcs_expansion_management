from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.models import ChargingStation, Evse, Organization, Program, Site
from app.features.pm.constants import (
    ApprovalStatus,
    ContractStatus,
    ContractType,
    DeliveryStatus,
    ImpactLevel,
    IssueKind,
    IssueStatus,
    PermitStatus,
    PlanScenario,
    ProjectStatus,
    ProjectType,
    PurchaseOrderStatus,
    StageExecutionStatus,
    TestOutcome,
)
from app.features.reference.models import ChargerType, ProjectStage, Region


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
    stages: Mapped[list[StageExecution]] = relationship(
        'StageExecution',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
        order_by='StageExecution.stage_no',
    )
    scopes: Mapped[list[ProjectScope]] = relationship(
        'ProjectScope',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    documents: Mapped[list[ProjectDocument]] = relationship(
        'ProjectDocument',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    permits: Mapped[list[Permit]] = relationship(
        'Permit',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    contracts: Mapped[list[Contract]] = relationship(
        'Contract',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship(
        'PurchaseOrder',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    construction_works: Mapped[list[ConstructionWork]] = relationship(
        'ConstructionWork',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    commissioning_tests: Mapped[list[CommissioningTest]] = relationship(
        'CommissioningTest',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    issues: Mapped[list[Issue]] = relationship(
        'Issue',
        back_populates='project',
        lazy='raise',
        cascade='all, delete-orphan',
    )

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
    lines: Mapped[list[NetworkPlanLine]] = relationship(
        'NetworkPlanLine',
        back_populates='network_plan',
        lazy='raise',
        cascade='all, delete-orphan',
        order_by='NetworkPlanLine.period_month',
    )

    def __repr__(self) -> str:
        return (
            f"NetworkPlan(version='{self.plan_version}', "
            f"scenario='{self.scenario}', status='{self.approval_status}')"
        )

    @property
    def is_approved(self) -> bool:
        return self.approval_status == ApprovalStatus.APPROVED


class NetworkPlanLine(TimestampMixin, Base):
    __tablename__ = 'network_plan_line'
    __table_args__ = (
        UniqueConstraint(
            'network_plan_id',
            'period_month',
            'region_id',
            'charger_type_id',
            name='uq_network_plan_line_plan_month_region_type',
        ),
        CheckConstraint(
            'EXTRACT(DAY FROM period_month) = 1',
            name='ck_network_plan_line_period_month_first_day',
        ),
        CheckConstraint(
            'planned_sites_with_type >= 0',
            name='ck_network_plan_line_sites_non_negative',
        ),
        CheckConstraint(
            'planned_new_stations >= 0',
            name='ck_network_plan_line_stations_non_negative',
        ),
        CheckConstraint(
            'planned_new_ports >= 0',
            name='ck_network_plan_line_ports_non_negative',
        ),
        CheckConstraint(
            'planned_new_power_kw >= 0',
            name='ck_network_plan_line_power_non_negative',
        ),
        CheckConstraint(
            'planned_capex_byn >= 0',
            name='ck_network_plan_line_capex_non_negative',
        ),
        Index('ix_network_plan_line_plan', 'network_plan_id'),
        Index('ix_network_plan_line_month', 'period_month'),
        {'schema': 'pm'},
    )

    network_plan_line_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique network plan line identifier',
    )
    network_plan_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.network_plan.network_plan_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the network plan',
    )
    period_month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment='Planning month (first day of month)',
    )
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('ref.region.region_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the region',
    )
    charger_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey('ref.charger_type.charger_type_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to charger type',
    )
    planned_sites_with_type: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Planned number of sites with this charger type',
    )
    planned_new_stations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Planned number of new charging stations',
    )
    planned_new_ports: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Planned number of new charging ports (EVSEs)',
    )
    planned_new_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        server_default='0',
        comment='Planned new power capacity in kW',
    )
    planned_capex_byn: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        server_default='0',
        comment='Planned CAPEX in BYN',
    )

    network_plan: Mapped[NetworkPlan] = relationship(
        'NetworkPlan',
        back_populates='lines',
        lazy='selectin',
    )
    region: Mapped[Region] = relationship(
        'Region',
        lazy='selectin',
    )
    charger_type: Mapped[ChargerType] = relationship(
        'ChargerType',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'NetworkPlanLine(month={self.period_month}, '
            f'region={self.region_id}, type={self.charger_type_id})'
        )


class ProjectScope(TimestampMixin, Base):
    __tablename__ = 'project_scope'
    __table_args__ = (
        CheckConstraint(
            'planned_stations >= 0',
            name='ck_project_scope_stations_non_negative',
        ),
        CheckConstraint(
            'planned_ports >= 0',
            name='ck_project_scope_ports_non_negative',
        ),
        CheckConstraint(
            'planned_power_kw >= 0',
            name='ck_project_scope_power_non_negative',
        ),
        Index('ix_project_scope_project', 'project_id'),
        {'schema': 'pm'},
    )

    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Reference to the project',
    )
    charger_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey('ref.charger_type.charger_type_id', ondelete='RESTRICT'),
        primary_key=True,
        comment='Reference to charger type',
    )
    planned_stations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Planned number of stations of this type',
    )
    planned_ports: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Planned number of ports (EVSEs) of this type',
    )
    planned_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        server_default='0',
        comment='Planned power capacity in kW for this type',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='scopes',
        lazy='selectin',
    )
    charger_type: Mapped[ChargerType] = relationship(
        'ChargerType',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'ProjectScope(project={self.project_id}, '
            f'type={self.charger_type_id}, stations={self.planned_stations})'
        )

    @property
    def average_power_per_station_kw(self) -> Decimal | None:
        if self.planned_stations > 0:
            return self.planned_power_kw / self.planned_stations
        return None


class StageExecution(TimestampMixin, Base):
    __tablename__ = 'stage_execution'
    __table_args__ = (
        UniqueConstraint(
            'project_id',
            'stage_no',
            name='uq_stage_execution_project_stage',
        ),
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in StageExecutionStatus)})',
            name='ck_stage_execution_status_valid',
        ),
        CheckConstraint(
            'baseline_finish IS NULL OR baseline_start IS NULL OR baseline_finish >= baseline_start',
            name='ck_stage_execution_baseline_valid',
        ),
        CheckConstraint(
            'actual_finish IS NULL OR actual_start IS NULL OR actual_finish >= actual_start',
            name='ck_stage_execution_actual_valid',
        ),
        Index('ix_stage_execution_project', 'project_id'),
        Index('ix_stage_execution_status', 'status'),
        Index('ix_stage_execution_stage_no', 'stage_no'),
        Index('ix_stage_status_due', 'status', 'forecast_finish'),
        {'schema': 'pm'},
    )

    stage_execution_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique stage execution identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    stage_no: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey('ref.project_stage.stage_no', ondelete='RESTRICT'),
        nullable=False,
        comment='Stage number (0-13)',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=StageExecutionStatus.NOT_STARTED,
        comment=f'Stage status: {", ".join(s.value for s in StageExecutionStatus)}',
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
        comment='Current forecasted finish date',
    )
    actual_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual start date',
    )
    actual_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual finish date',
    )
    responsible_organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Responsible organization for this stage',
    )
    gate_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when gate was approved',
    )
    gate_approved_by: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='User ID who approved the gate',
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Comments or notes for this stage',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='stages',
        lazy='selectin',
    )
    stage: Mapped[ProjectStage] = relationship(
        'ProjectStage',
        lazy='selectin',
    )
    responsible_organization: Mapped[Organization | None] = relationship(
        'Organization',
        lazy='selectin',
    )
    documents: Mapped[list[ProjectDocument]] = relationship(
        'ProjectDocument',
        back_populates='stage_execution',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    permits: Mapped[list[Permit]] = relationship(
        'Permit',
        back_populates='stage_execution',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    commissioning_tests: Mapped[list[CommissioningTest]] = relationship(
        'CommissioningTest',
        back_populates='stage_execution',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    issues: Mapped[list[Issue]] = relationship(
        'Issue',
        back_populates='stage_execution',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    successor_dependencies: Mapped[list[StageDependency]] = relationship(
        'StageDependency',
        foreign_keys='StageDependency.predecessor_stage_id',
        back_populates='predecessor_stage',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    predecessor_dependencies: Mapped[list[StageDependency]] = relationship(
        'StageDependency',
        foreign_keys='StageDependency.successor_stage_id',
        back_populates='successor_stage',
        lazy='raise',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return (
            f'StageExecution(project={self.project_id}, '
            f"stage={self.stage_no}, status='{self.status}')"
        )

    @property
    def is_completed(self) -> bool:
        return self.status in (
            StageExecutionStatus.APPROVED,
            StageExecutionStatus.APPROVED_CONDITIONS,
            StageExecutionStatus.CANCELLED,
        )

    @property
    def is_blocked(self) -> bool:
        return self.status == StageExecutionStatus.BLOCKED

    @property
    def is_in_progress(self) -> bool:
        return self.status in (
            StageExecutionStatus.IN_PROGRESS,
            StageExecutionStatus.AWAITING_INPUT,
            StageExecutionStatus.READY_FOR_GATE,
            StageExecutionStatus.REWORK,
        )

    @property
    def delay_days(self) -> int | None:
        if self.forecast_finish and self.baseline_finish:
            return (self.forecast_finish - self.baseline_finish).days
        return None

    @property
    def actual_duration_days(self) -> int | None:
        if self.actual_start and self.actual_finish:
            return (self.actual_finish - self.actual_start).days
        return None


class StageDependency(TimestampMixin, Base):
    __tablename__ = 'stage_dependency'
    __table_args__ = (
        CheckConstraint(
            'predecessor_stage_id <> successor_stage_id',
            name='ck_stage_dependency_no_self_reference',
        ),
        CheckConstraint(
            'lag_days >= 0',
            name='ck_stage_dependency_lag_non_negative',
        ),
        Index('ix_stage_dependency_predecessor', 'predecessor_stage_id'),
        Index('ix_stage_dependency_successor', 'successor_stage_id'),
        {'schema': 'pm'},
    )

    predecessor_stage_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.stage_execution.stage_execution_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Predecessor stage (must finish before successor starts)',
    )
    successor_stage_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.stage_execution.stage_execution_id', ondelete='CASCADE'),
        primary_key=True,
        comment='Successor stage (starts after predecessor finishes)',
    )
    lag_days: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default='0',
        comment='Lag in days between predecessor finish and successor start',
    )

    predecessor_stage: Mapped[StageExecution] = relationship(
        'StageExecution',
        foreign_keys='StageDependency.predecessor_stage_id',
        back_populates='successor_dependencies',
        lazy='selectin',
    )
    successor_stage: Mapped[StageExecution] = relationship(
        'StageExecution',
        foreign_keys='StageDependency.successor_stage_id',
        back_populates='predecessor_dependencies',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'StageDependency(predecessor={self.predecessor_stage_id}, '
            f'successor={self.successor_stage_id}, lag={self.lag_days})'
        )


class ProjectDocument(TimestampMixin, Base):
    __tablename__ = 'project_document'
    __table_args__ = (
        CheckConstraint(
            'revision_no > 0',
            name='ck_project_document_revision_positive',
        ),
        Index('ix_project_document_project', 'project_id'),
        Index('ix_project_document_stage', 'stage_execution_id'),
        Index('ix_project_document_type', 'doc_type'),
        Index('ix_project_document_edms', 'edms_document_id'),
        {'schema': 'pm'},
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique document identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    stage_execution_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.stage_execution.stage_execution_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the stage this document belongs to',
    )
    doc_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Document type (e.g., "PERMIT", "CONTRACT", "DESIGN")',
    )
    doc_number: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Official document number',
    )
    document_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Document date',
    )
    edms_document_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Document ID in corporate EDMS system',
    )
    document_uri: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='URI or path to the document file',
    )
    revision_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1',
        comment='Document revision number',
    )
    is_mandatory: Mapped[bool] = mapped_column(
        nullable=False,
        server_default='false',
        comment='Whether this document is mandatory for gate approval',
    )
    accepted: Mapped[bool] = mapped_column(
        nullable=False,
        server_default='false',
        comment='Whether this document has been accepted/approved',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='documents',
        lazy='selectin',
    )
    stage_execution: Mapped[StageExecution | None] = relationship(
        'StageExecution',
        lazy='selectin',
    )
    permits: Mapped[list[Permit]] = relationship(
        'Permit',
        back_populates='document',
        lazy='raise',
    )
    commissioning_tests: Mapped[list[CommissioningTest]] = relationship(
        'CommissioningTest',
        back_populates='document',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return (
            f"ProjectDocument(type='{self.doc_type}', "
            f"number='{self.doc_number}', revision={self.revision_no})"
        )

    @property
    def is_accepted(self) -> bool:
        return self.accepted

    @property
    def is_mandatory_and_not_accepted(self) -> bool:
        return self.is_mandatory and not self.accepted


class Permit(TimestampMixin, Base):
    __tablename__ = 'permit'
    __table_args__ = (
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in PermitStatus)})',
            name='ck_permit_status_valid',
        ),
        Index('ix_permit_project', 'project_id'),
        Index('ix_permit_due', 'due_date', 'status'),
        {'schema': 'pm'},
    )

    permit_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique permit identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    permit_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Type of permit (e.g., "BUILDING_PERMIT", "ENVIRONMENTAL")',
    )
    issuing_authority: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Authority issuing the permit',
    )
    application_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Date when permit application was submitted',
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Expected date for permit issuance',
    )
    received_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual date when permit was received',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=PermitStatus.NOT_STARTED,
        comment=f'Permit status: {", ".join(s.value for s in PermitStatus)}',
    )
    document_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.project_document.document_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the permit document',
    )
    responsible_organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Organization responsible for obtaining this permit',
    )
    blocking: Mapped[bool] = mapped_column(
        nullable=False,
        server_default='true',
        comment='Whether this permit blocks the gate approval',
    )
    delay_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Reason for delay in obtaining permit',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='permits',
        lazy='selectin',
    )
    document: Mapped[ProjectDocument | None] = relationship(
        'ProjectDocument',
        lazy='selectin',
    )
    responsible_organization: Mapped[Organization | None] = relationship(
        'Organization',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f"Permit(type='{self.permit_type}', "
            f"status='{self.status}', blocking={self.blocking})"
        )

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status not in (
            PermitStatus.APPROVED,
            PermitStatus.EXPIRED,
        ):
            return date.today() > self.due_date
        return False

    @property
    def is_blocking_and_not_approved(self) -> bool:
        return self.blocking and self.status != PermitStatus.APPROVED


class Contract(TimestampMixin, Base):
    __tablename__ = 'contract'
    __table_args__ = (
        UniqueConstraint(
            'erp_contract_id',
            name='uq_contract_erp_id',
        ),
        CheckConstraint(
            f'contract_type IN ({",".join(repr(t.value) for t in ContractType)})',
            name='ck_contract_type_valid',
        ),
        CheckConstraint(
            f'contract_status IN ({",".join(repr(s.value) for s in ContractStatus)})',
            name='ck_contract_status_valid',
        ),
        CheckConstraint(
            'contract_value_byn >= 0',
            name='ck_contract_value_non_negative',
        ),
        CheckConstraint(
            'actual_finish IS NULL OR signed_on IS NULL OR actual_finish >= signed_on',
            name='ck_contract_finish_after_signed',
        ),
        Index('ix_contract_project', 'project_id'),
        Index('ix_contract_vendor', 'vendor_id'),
        {'schema': 'pm'},
    )

    contract_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique contract identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    contract_no: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Internal contract number',
    )
    erp_contract_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Contract ID in corporate ERP system',
    )
    contract_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=f'Contract type: {", ".join(t.value for t in ContractType)}',
    )
    vendor_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the vendor/contractor organization',
    )
    signed_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Date when contract was signed',
    )
    planned_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned contract finish date',
    )
    actual_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual contract finish date',
    )
    contract_value_byn: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment='Total contract value in BYN',
    )
    contract_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=ContractStatus.DRAFT,
        comment=f'Contract status: {", ".join(s.value for s in ContractStatus)}',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='contracts',
        lazy='selectin',
    )
    vendor: Mapped[Organization | None] = relationship(
        'Organization',
        lazy='selectin',
    )
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship(
        'PurchaseOrder',
        back_populates='contract',
        lazy='raise',
        cascade='all, delete-orphan',
    )
    construction_works: Mapped[list[ConstructionWork]] = relationship(
        'ConstructionWork',
        back_populates='contract',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return (
            f"Contract(no='{self.contract_no}', "
            f"type='{self.contract_type}', status='{self.contract_status}')"
        )

    @property
    def is_active(self) -> bool:
        return self.contract_status == ContractStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.contract_status == ContractStatus.COMPLETED


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = 'purchase_order'
    __table_args__ = (
        UniqueConstraint(
            'erp_po_id',
            name='uq_purchase_order_erp_id',
        ),
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in PurchaseOrderStatus)})',
            name='ck_purchase_order_status_valid',
        ),
        CheckConstraint(
            'order_amount_byn >= 0',
            name='ck_purchase_order_amount_non_negative',
        ),
        Index('ix_purchase_order_project', 'project_id'),
        Index('ix_purchase_order_contract', 'contract_id'),
        {'schema': 'pm'},
    )

    po_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique purchase order identifier',
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
        comment='Reference to the contract',
    )
    po_number: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Internal purchase order number',
    )
    erp_po_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Purchase order ID in corporate ERP system',
    )
    ordered_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Date when order was placed',
    )
    planned_delivery: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned delivery date',
    )
    order_amount_byn: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment='Total order amount in BYN',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=PurchaseOrderStatus.ORDERED,
        comment=f'Purchase order status: {", ".join(s.value for s in PurchaseOrderStatus)}',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='purchase_orders',
        lazy='selectin',
    )
    contract: Mapped[Contract | None] = relationship(
        'Contract',
        lazy='selectin',
    )
    deliveries: Mapped[list[Delivery]] = relationship(
        'Delivery',
        back_populates='purchase_order',
        lazy='raise',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f"PurchaseOrder(no='{self.po_number}', status='{self.status}')"

    @property
    def is_delivered(self) -> bool:
        return self.status == PurchaseOrderStatus.DELIVERED


class Delivery(TimestampMixin, Base):
    __tablename__ = 'delivery'
    __table_args__ = (
        CheckConstraint(
            f'delivery_status IN ({",".join(repr(s.value) for s in DeliveryStatus)})',
            name='ck_delivery_status_valid',
        ),
        Index('ix_delivery_po', 'po_id'),
        {'schema': 'pm'},
    )

    delivery_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique delivery identifier',
    )
    po_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.purchase_order.po_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the purchase order',
    )
    delivered_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual delivery date',
    )
    delivery_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Delivery note number or reference',
    )
    delivery_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=DeliveryStatus.IN_TRANSIT,
        comment=f'Delivery status: {", ".join(s.value for s in DeliveryStatus)}',
    )
    acceptance_document_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.project_document.document_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the acceptance document',
    )

    purchase_order: Mapped[PurchaseOrder] = relationship(
        'PurchaseOrder',
        back_populates='deliveries',
        lazy='selectin',
    )
    acceptance_document: Mapped[ProjectDocument | None] = relationship(
        'ProjectDocument',
        lazy='selectin',
    )
    items: Mapped[list[DeliveryItem]] = relationship(
        'DeliveryItem',
        back_populates='delivery',
        lazy='selectin',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f"Delivery(id={self.delivery_id}, status='{self.delivery_status}')"

    @property
    def is_accepted(self) -> bool:
        return self.delivery_status == DeliveryStatus.ACCEPTED


class DeliveryItem(TimestampMixin, Base):
    __tablename__ = 'delivery_item'
    __table_args__ = (
        CheckConstraint(
            'quantity > 0',
            name='ck_delivery_item_quantity_positive',
        ),
        Index('ix_delivery_item_delivery', 'delivery_id'),
        Index('ix_delivery_item_station', 'station_id'),
        {'schema': 'pm'},
    )

    delivery_item_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique delivery item identifier',
    )
    delivery_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.delivery.delivery_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the delivery',
    )
    equipment_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Name or description of the equipment',
    )
    serial_number: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Serial number of the equipment',
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1',
        comment='Quantity of items',
    )
    station_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the charging station this equipment belongs to',
    )

    delivery: Mapped[Delivery] = relationship(
        'Delivery',
        back_populates='items',
        lazy='selectin',
    )
    station: Mapped[ChargingStation | None] = relationship(
        'ChargingStation',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f"DeliveryItem(name='{self.equipment_name}', "
            f"serial='{self.serial_number}', qty={self.quantity})"
        )


class ConstructionWork(TimestampMixin, Base):
    __tablename__ = 'construction_work'
    __table_args__ = (
        CheckConstraint(
            'weight_pct >= 0 AND weight_pct <= 100',
            name='ck_construction_work_weight_valid',
        ),
        CheckConstraint(
            'progress_pct >= 0 AND progress_pct <= 100',
            name='ck_construction_work_progress_valid',
        ),
        CheckConstraint(
            'planned_finish IS NULL OR planned_start IS NULL OR planned_finish >= planned_start',
            name='ck_construction_work_planned_valid',
        ),
        CheckConstraint(
            'actual_finish IS NULL OR actual_start IS NULL OR actual_finish >= actual_start',
            name='ck_construction_work_actual_valid',
        ),
        Index('ix_construction_work_project', 'project_id'),
        Index('ix_construction_work_contract', 'contract_id'),
        {'schema': 'pm'},
    )

    work_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique construction work identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    work_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Type of construction work (e.g., "FOUNDATION", "ELECTRICAL", "CIVIL")',
    )
    weight_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
        comment='Weight percentage in overall project completion (0-100)',
    )
    planned_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned start date',
    )
    planned_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned finish date',
    )
    actual_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual start date',
    )
    actual_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual finish date',
    )
    progress_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 3),
        nullable=False,
        server_default='0',
        comment='Current progress percentage (0-100)',
    )
    accepted: Mapped[bool] = mapped_column(
        nullable=False,
        server_default='false',
        comment='Whether this work package has been accepted',
    )
    contract_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.contract.contract_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the construction contract',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='construction_works',
        lazy='selectin',
    )
    contract: Mapped[Contract | None] = relationship(
        'Contract',
        back_populates='construction_works',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f"ConstructionWork(type='{self.work_type}', "
            f'progress={self.progress_pct}%, accepted={self.accepted})'
        )

    @property
    def is_completed(self) -> bool:
        return self.accepted or self.progress_pct >= 100

    @property
    def weighted_progress_pct(self) -> Decimal:
        if self.weight_pct is not None:
            return (self.weight_pct * self.progress_pct) / Decimal('100')
        return Decimal('0')


class CommissioningTest(TimestampMixin, Base):
    __tablename__ = 'commissioning_test'
    __table_args__ = (
        CheckConstraint(
            f'outcome IN ({",".join(repr(o.value) for o in TestOutcome)})',
            name='ck_commissioning_test_outcome_valid',
        ),
        Index('ix_commissioning_test_project', 'project_id'),
        Index('ix_commissioning_test_evse', 'evse_id'),
        {'schema': 'pm'},
    )

    test_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique test identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    evse_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the EVSE being tested',
    )
    test_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Test code or name (e.g., "SAFETY_CHECK", "POWER_TEST")',
    )
    tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when test was performed',
    )
    outcome: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=TestOutcome.PENDING,
        comment=f'Test outcome: {", ".join(o.value for o in TestOutcome)}',
    )
    document_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.project_document.document_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the test report document',
    )
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Remarks or comments about the test',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='commissioning_tests',
        lazy='selectin',
    )
    stage_execution: Mapped[StageExecution | None] = relationship(
        'StageExecution',
        back_populates='commissioning_tests',
        lazy='selectin',
    )
    evse: Mapped[Evse | None] = relationship(
        'Evse',
        lazy='selectin',
    )
    document: Mapped[ProjectDocument | None] = relationship(
        'ProjectDocument',
        back_populates='commissioning_tests',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f"CommissioningTest(code='{self.test_code}', outcome='{self.outcome}')"

    @property
    def is_passed(self) -> bool:
        return self.outcome == TestOutcome.PASS

    @property
    def is_failed(self) -> bool:
        return self.outcome == TestOutcome.FAIL

    @property
    def is_waived(self) -> bool:
        return self.outcome == TestOutcome.WAIVED


class Issue(TimestampMixin, Base):
    __tablename__ = 'issue'
    __table_args__ = (
        CheckConstraint(
            f'kind IN ({",".join(repr(k.value) for k in IssueKind)})',
            name='ck_issue_kind_valid',
        ),
        CheckConstraint(
            f'impact_level IN ({",".join(repr(level.value) for level in ImpactLevel)})',
            name='ck_issue_impact_level_valid',
        ),
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in IssueStatus)})',
            name='ck_issue_status_valid',
        ),
        CheckConstraint(
            'estimated_cost_byn IS NULL OR estimated_cost_byn >= 0',
            name='ck_issue_estimated_cost_non_negative',
        ),
        Index('ix_issue_project', 'project_id'),
        Index('ix_issue_stage', 'stage_execution_id'),
        Index('ix_issue_kind', 'kind'),
        Index('ix_issue_status', 'status'),
        {'schema': 'pm'},
    )

    issue_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique issue identifier',
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('pm.project.project_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the project',
    )
    stage_execution_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('pm.stage_execution.stage_execution_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the stage this issue relates to',
    )
    kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=f'Issue kind: {", ".join(k.value for k in IssueKind)}',
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Issue title or short description',
    )
    impact_level: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=f'Impact level: {", ".join(level.value for level in ImpactLevel)}',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=IssueStatus.OPEN,
        comment=f'Issue status: {", ".join(s.value for s in IssueStatus)}',
    )
    owner_organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Organization responsible for resolving this issue',
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Target date for resolution',
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Timestamp when issue was opened',
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when issue was closed',
    )
    estimated_delay_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment='Estimated delay in days caused by this issue',
    )
    estimated_cost_byn: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment='Estimated additional cost in BYN',
    )

    project: Mapped[Project] = relationship(
        'Project',
        back_populates='issues',
        lazy='selectin',
    )
    stage_execution: Mapped[StageExecution | None] = relationship(
        'StageExecution',
        back_populates='issues',
        lazy='selectin',
    )
    owner_organization: Mapped[Organization | None] = relationship(
        'Organization',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f"Issue(kind='{self.kind}', title='{self.title}', status='{self.status}')"
        )

    @property
    def is_open(self) -> bool:
        return self.status in (IssueStatus.OPEN, IssueStatus.IN_PROGRESS)

    @property
    def is_critical(self) -> bool:
        return self.impact_level == ImpactLevel.CRITICAL

    @property
    def duration_days(self) -> int | None:
        if self.opened_at and self.closed_at:
            return (self.closed_at - self.opened_at).days
        return None
