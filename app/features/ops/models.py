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
    desc,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.models import ChargingStation, Connector, Evse
from app.features.integration.models import SourceSystem
from app.features.ops.constants import ChargingSessionStatus, Severity


class ChargingSession(TimestampMixin, Base):
    __tablename__ = 'charging_session'
    __table_args__ = (
        UniqueConstraint(
            'source_system_id',
            'external_session_id',
            name='uq_charging_session_source_external',
        ),
        CheckConstraint(
            f'session_status IN ({",".join(repr(s.value) for s in ChargingSessionStatus)})',
            name='charging_session_status_valid',
        ),
        CheckConstraint(
            'energy_kwh IS NULL OR energy_kwh >= 0',
            name='charging_session_energy_non_negative',
        ),
        CheckConstraint(
            'ended_at IS NULL OR ended_at >= started_at',
            name='charging_session_period_valid',
        ),
        Index('ix_session_evse_start', 'evse_id', desc('started_at')),
        Index('ix_session_started', desc('started_at')),
        {'schema': 'ops'},
    )

    session_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique charging session identifier',
    )
    source_system_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            'integration.source_system.source_system_id',
            ondelete='RESTRICT',
        ),
        nullable=False,
        comment='External system that emitted this session (typically the incumbent CPMS)',
    )
    external_session_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Session identifier as used by the external system (idempotency key)',
    )
    evse_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the EVSE where the session took place',
    )
    connector_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.connector.connector_id', ondelete='SET NULL'),
        nullable=True,
        comment='Optional reference to the specific connector used',
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment='Session start timestamp',
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Session end timestamp (NULL if still in progress)',
    )
    energy_kwh: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        comment='Energy delivered in kWh (NULL while session is in progress)',
    )
    session_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=f'Session status: {", ".join(s.value for s in ChargingSessionStatus)}',
    )
    tariff_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=(
            'Technical/operational tariff attribute. NOT the final revenue. '
            'Revenue is determined by the billing system and aggregated in finance.revenue_entry'
        ),
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='When the session was received into the national system',
    )

    source_system: Mapped[SourceSystem] = relationship(
        'SourceSystem',
        lazy='selectin',
    )
    evse: Mapped[Evse] = relationship(
        'Evse',
        lazy='raise',
    )
    connector: Mapped[Connector | None] = relationship(
        'Connector',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return (
            f'ChargingSession(session_id={self.session_id}, '
            f"external='{self.external_session_id}', status='{self.session_status}')"
        )

    @property
    def is_in_progress(self) -> bool:
        return self.ended_at is None

    @property
    def duration_minutes(self) -> float | None:
        if self.ended_at is None or self.started_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds() / 60


class EvseDaily(TimestampMixin, Base):
    __tablename__ = 'evse_daily'
    __table_args__ = (
        CheckConstraint(
            'service_minutes BETWEEN 0 AND 1440',
            name='evse_daily_service_minutes_valid',
        ),
        CheckConstraint(
            'available_minutes BETWEEN 0 AND 1440',
            name='evse_daily_available_minutes_valid',
        ),
        CheckConstraint(
            'outage_minutes BETWEEN 0 AND 1440',
            name='evse_daily_outage_minutes_valid',
        ),
        CheckConstraint(
            'energy_kwh >= 0',
            name='evse_daily_energy_non_negative',
        ),
        CheckConstraint(
            'sessions_count >= 0',
            name='evse_daily_sessions_count_non_negative',
        ),
        CheckConstraint(
            'power_kw_snapshot > 0',
            name='evse_daily_power_snapshot_positive',
        ),
        CheckConstraint(
            'available_minutes + outage_minutes <= service_minutes',
            name='evse_daily_minutes_consistency',
        ),
        Index('ix_evse_daily_date', 'service_date'),
        {'schema': 'ops'},
    )

    evse_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='RESTRICT'),
        primary_key=True,
        comment='Reference to the EVSE',
    )
    service_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        comment='Service date (one row per EVSE per day)',
    )
    service_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Total service minutes in the day (0..1440)',
    )
    available_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Available minutes, including busy operational EVSE (0..1440)',
    )
    outage_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Outage/unavailability minutes (0..1440)',
    )
    energy_kwh: Mapped[Decimal] = mapped_column(
        Numeric(16, 4),
        nullable=False,
        server_default='0',
        comment='Total energy delivered in kWh',
    )
    sessions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='0',
        comment='Number of charging sessions',
    )
    power_kw_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        comment='Nominal power snapshot in kW (used for utilization calculation)',
    )
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='When this daily record was last refreshed',
    )

    evse: Mapped[Evse] = relationship(
        'Evse',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return (
            f'EvseDaily(evse_id={self.evse_id}, date={self.service_date}, '
            f'energy={self.energy_kwh} kWh)'
        )

    @property
    def availability_pct(self) -> Decimal | None:
        if self.service_minutes == 0:
            return None
        return (
            Decimal(self.available_minutes) / Decimal(self.service_minutes)
        ) * Decimal('100')

    @property
    def utilization_pct(self) -> Decimal | None:
        if self.power_kw_snapshot <= 0 or self.service_minutes == 0:
            return None
        theoretical_kwh = (
            self.power_kw_snapshot * Decimal(self.service_minutes) / Decimal('60')
        )
        if theoretical_kwh == 0:
            return None
        return (self.energy_kwh / theoretical_kwh) * Decimal('100')


class Outage(TimestampMixin, Base):
    __tablename__ = 'outage'
    __table_args__ = (
        CheckConstraint(
            f'severity IS NULL OR severity IN ({",".join(repr(s.value) for s in Severity)})',
            name='outage_severity_valid',
        ),
        CheckConstraint(
            'ended_at IS NULL OR ended_at > started_at',
            name='outage_period_valid',
        ),
        Index('ix_outage_evse_start', 'evse_id', desc('started_at')),
        {'schema': 'ops'},
    )

    outage_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique outage identifier',
    )
    evse_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the EVSE that was out of service',
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment='Outage start timestamp',
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Outage end timestamp (NULL if still ongoing)',
    )
    reason_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Reason code for the outage',
    )
    severity: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=f'Outage severity: {", ".join(s.value for s in Severity)}',
    )
    external_incident_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='External incident identifier from the source system',
    )

    evse: Mapped[Evse] = relationship(
        'Evse',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return (
            f'Outage(outage_id={self.outage_id}, evse_id={self.evse_id}, '
            f'started_at={self.started_at})'
        )

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def duration_minutes(self) -> float | None:
        if self.ended_at is None or self.started_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds() / 60


class Alarm(TimestampMixin, Base):
    __tablename__ = 'alarm'
    __table_args__ = (
        UniqueConstraint(
            'source_system_id',
            'external_alarm_id',
            name='uq_alarm_source_external',
        ),
        CheckConstraint(
            f'severity IS NULL OR severity IN ({",".join(repr(s.value) for s in Severity)})',
            name='alarm_severity_valid',
        ),
        CheckConstraint(
            'cleared_at IS NULL OR cleared_at >= started_at',
            name='alarm_period_valid',
        ),
        Index('ix_alarm_station_started', 'station_id', desc('started_at')),
        {'schema': 'ops'},
    )

    alarm_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique alarm identifier',
    )
    station_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='RESTRICT'),
        nullable=False,
        comment='Reference to the charging station',
    )
    evse_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='SET NULL'),
        nullable=True,
        comment='Optional reference to the specific EVSE involved',
    )
    source_system_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            'integration.source_system.source_system_id',
            ondelete='SET NULL',
        ),
        nullable=True,
        comment='Source system that emitted the alarm',
    )
    external_alarm_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Alarm identifier as used by the external system (idempotency key)',
    )
    alarm_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Alarm code (e.g., OCPP error code)',
    )
    severity: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=f'Alarm severity: {", ".join(s.value for s in Severity)}',
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment='Alarm start timestamp',
    )
    cleared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Alarm clearance timestamp (NULL if still active)',
    )

    station: Mapped[ChargingStation] = relationship(
        'ChargingStation',
        lazy='raise',
    )
    evse: Mapped[Evse | None] = relationship(
        'Evse',
        lazy='raise',
    )
    source_system: Mapped[SourceSystem | None] = relationship(
        'SourceSystem',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'Alarm(alarm_id={self.alarm_id}, station_id={self.station_id}, '
            f"code='{self.alarm_code}')"
        )

    @property
    def is_active(self) -> bool:
        return self.cleared_at is None

    @property
    def duration_minutes(self) -> float | None:
        if self.cleared_at is None or self.started_at is None:
            return None
        return (self.cleared_at - self.started_at).total_seconds() / 60
