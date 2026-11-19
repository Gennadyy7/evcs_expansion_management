from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.models import ChargingStation, Connector, Evse, Site
from app.features.integration.constants import (
    EntityKind,
    InboxEventStatus,
    IngestionBatchStatus,
    SourceSystemKind,
)

# Derived from EntityKind to prevent DDL drift; single-line to avoid Alembic diff noise.
_ENTITY_KIND_EXPRESSION = (
    'CASE '
    f"WHEN site_id IS NOT NULL THEN '{EntityKind.SITE.value}' "
    f"WHEN station_id IS NOT NULL THEN '{EntityKind.STATION.value}' "
    f"WHEN evse_id IS NOT NULL THEN '{EntityKind.EVSE.value}' "
    f"WHEN connector_id IS NOT NULL THEN '{EntityKind.CONNECTOR.value}' "
    'END'
)


class SourceSystem(TimestampMixin, Base):
    __tablename__ = 'source_system'
    __table_args__ = (
        UniqueConstraint('code', name='uq_source_system_code'),
        CheckConstraint(
            f'system_kind IN ({",".join(repr(k.value) for k in SourceSystemKind)})',
            name='kind_valid',
        ),
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
        comment='Stable short key used by services and seeds (CPMS, ERP, BILLING, ...)',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='System name in Russian',
    )
    system_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=f'System classification: {", ".join(k.value for k in SourceSystemKind)}',
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default='true',
        comment='Whether ingestion from this system is currently enabled',
    )

    external_identities: Mapped[list[ExternalIdentity]] = relationship(
        'ExternalIdentity',
        back_populates='source_system',
        lazy='raise',
    )
    ingestion_batches: Mapped[list[IngestionBatch]] = relationship(
        'IngestionBatch',
        back_populates='source_system',
        lazy='raise',
        order_by='IngestionBatch.started_at.desc()',
    )
    inbox_events: Mapped[list[InboxEvent]] = relationship(
        'InboxEvent',
        back_populates='source_system',
        lazy='raise',
    )

    def __repr__(self) -> str:
        return f"SourceSystem(code='{self.code}', kind='{self.system_kind}', active={self.is_active})"


class ExternalIdentity(TimestampMixin, Base):
    __tablename__ = 'external_identity'
    __table_args__ = (
        UniqueConstraint(
            'source_system_id',
            'entity_kind',
            'external_id',
            name='uq_external_identity_source_kind_external',
        ),
        CheckConstraint(
            'num_nonnulls(site_id, station_id, evse_id, connector_id) = 1',
            name='exactly_one_target',
        ),
        Index('ix_mapping_evse', 'evse_id'),
        Index('ix_mapping_station', 'station_id'),
        Index('ix_mapping_site', 'site_id'),
        Index('ix_mapping_connector', 'connector_id'),
        Index('ix_mapping_source_external', 'source_system_id', 'external_id'),
        {'schema': 'integration'},
    )

    mapping_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique identity mapping identifier',
    )
    source_system_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            'integration.source_system.source_system_id',
            ondelete='RESTRICT',
        ),
        nullable=False,
        comment='External system that owns this identifier',
    )
    external_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Identifier as used by the external system',
    )
    site_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=True,
        comment='Target site (mutually exclusive with station/evse/connector)',
    )
    station_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.charging_station.station_id', ondelete='CASCADE'),
        nullable=True,
        comment='Target charging station (mutually exclusive)',
    )
    evse_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.evse.evse_id', ondelete='CASCADE'),
        nullable=True,
        comment='Target EVSE (mutually exclusive)',
    )
    connector_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey('core.connector.connector_id', ondelete='CASCADE'),
        nullable=True,
        comment='Target connector (mutually exclusive)',
    )
    entity_kind: Mapped[str | None] = mapped_column(
        Text,
        Computed(_ENTITY_KIND_EXPRESSION, persisted=True),
        nullable=True,
        comment=(
            'Database-generated target kind: '
            f'{", ".join(k.value for k in EntityKind)}. '
            'Read-only; derived from the filled target column'
        ),
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='When the mapping was registered',
    )

    source_system: Mapped[SourceSystem] = relationship(
        'SourceSystem',
        back_populates='external_identities',
        lazy='selectin',
    )
    # Mutually exclusive targets: lazy='raise' avoids 3 wasted SELECTs per row.
    site: Mapped[Site | None] = relationship('Site', lazy='raise')
    station: Mapped[ChargingStation | None] = relationship(
        'ChargingStation', lazy='raise'
    )
    evse: Mapped[Evse | None] = relationship('Evse', lazy='raise')
    connector: Mapped[Connector | None] = relationship('Connector', lazy='raise')

    def __repr__(self) -> str:
        return (
            f'ExternalIdentity(source={self.source_system_id}, '
            f"external='{self.external_id}', kind='{self.target_kind}')"
        )

    @property
    def target_kind(self) -> EntityKind | None:
        if self.site_id is not None:
            return EntityKind.SITE
        if self.station_id is not None:
            return EntityKind.STATION
        if self.evse_id is not None:
            return EntityKind.EVSE
        if self.connector_id is not None:
            return EntityKind.CONNECTOR
        return None

    @property
    def target_entity_id(self) -> UUID | None:
        if self.site_id is not None:
            return self.site_id
        if self.station_id is not None:
            return self.station_id
        if self.evse_id is not None:
            return self.evse_id
        if self.connector_id is not None:
            return self.connector_id
        return None


class IngestionBatch(TimestampMixin, Base):
    __tablename__ = 'ingestion_batch'
    __table_args__ = (
        CheckConstraint(
            f'status IN ({",".join(repr(s.value) for s in IngestionBatchStatus)})',
            name='status_valid',
        ),
        CheckConstraint(
            'records_received >= 0',
            name='records_received_non_negative',
        ),
        CheckConstraint(
            'records_failed >= 0',
            name='records_failed_non_negative',
        ),
        CheckConstraint(
            'ended_at IS NULL OR ended_at >= started_at',
            name='period_valid',
        ),
        Index(
            'ix_ingestion_batch_source_started', 'source_system_id', desc('started_at')
        ),
        Index('ix_ingestion_batch_status', 'status'),
        {'schema': 'integration'},
    )

    batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique ingestion batch identifier',
    )
    source_system_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            'integration.source_system.source_system_id',
            ondelete='RESTRICT',
        ),
        nullable=False,
        comment='System the batch was loaded from',
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Batch start timestamp',
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Batch completion timestamp (NULL while running)',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=IngestionBatchStatus.RUNNING,
        comment=f'Batch status: {", ".join(s.value for s in IngestionBatchStatus)}',
    )
    records_received: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0',
        comment='Number of records received from the source',
    )
    records_failed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0',
        comment='Number of records rejected during validation/application',
    )
    watermark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Opaque incremental-read position, format defined by the connector',
    )

    source_system: Mapped[SourceSystem] = relationship(
        'SourceSystem',
        back_populates='ingestion_batches',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'IngestionBatch(source={self.source_system_id}, '
            f"status='{self.status}', received={self.records_received}, "
            f'failed={self.records_failed})'
        )

    @property
    def is_running(self) -> bool:
        return self.status == IngestionBatchStatus.RUNNING

    @property
    def is_finished(self) -> bool:
        return self.status in (
            IngestionBatchStatus.COMPLETED,
            IngestionBatchStatus.PARTIAL,
            IngestionBatchStatus.FAILED,
            IngestionBatchStatus.CANCELLED,
        )

    @property
    def records_succeeded(self) -> int:
        return max(0, self.records_received - self.records_failed)

    @property
    def failure_rate_pct(self) -> Decimal | None:
        if self.records_received <= 0:
            return None
        return (
            Decimal(self.records_failed) / Decimal(self.records_received)
        ) * Decimal('100')

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None or self.started_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


class InboxEvent(TimestampMixin, Base):
    __tablename__ = 'inbox_event'
    __table_args__ = (
        UniqueConstraint(
            'source_system_id',
            'external_event_key',
            name='uq_inbox_event_source_external_key',
        ),
        CheckConstraint(
            f'processing_status IN ({",".join(repr(s.value) for s in InboxEventStatus)})',
            name='processing_status_valid',
        ),
        Index('ix_inbox_pending', 'processing_status', 'received_at'),
        Index('ix_inbox_event_event_time', 'event_time'),
        {'schema': 'integration'},
    )

    inbox_event_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        comment='Unique inbox event identifier',
    )
    source_system_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            'integration.source_system.source_system_id',
            ondelete='RESTRICT',
        ),
        nullable=False,
        comment='System that emitted the event',
    )
    external_event_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Event key unique within the source system (idempotency key)',
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=(
            'Source-defined event type (open vocabulary, no DB CHECK): '
            'CHARGING_SESSION, EVSE_STATUS, ALARM, CAPEX_POSTED, ...'
        ),
    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment='Business timestamp of the event as reported by the source',
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='When the event was persisted into the inbox',
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        comment='Raw event payload as received; replay source of truth',
    )
    processing_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=InboxEventStatus.NEW,
        comment=f'Processing status: {", ".join(s.value for s in InboxEventStatus)}',
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Last processing error details (populated on FAILED)',
    )

    source_system: Mapped[SourceSystem] = relationship(
        'SourceSystem',
        back_populates='inbox_events',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f'InboxEvent(source={self.source_system_id}, '
            f"type='{self.event_type}', status='{self.processing_status}')"
        )

    @property
    def is_pending(self) -> bool:
        return self.processing_status == InboxEventStatus.NEW

    @property
    def is_processing(self) -> bool:
        return self.processing_status == InboxEventStatus.PROCESSING

    @property
    def is_processed(self) -> bool:
        return self.processing_status == InboxEventStatus.PROCESSED

    @property
    def is_failed(self) -> bool:
        return self.processing_status == InboxEventStatus.FAILED

    @property
    def is_retryable(self) -> bool:
        return self.processing_status == InboxEventStatus.FAILED
