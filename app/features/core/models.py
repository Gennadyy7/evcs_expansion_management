from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
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
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.features.core.constants import (
    CurrentKind,
    EvseLifecycleStatus,
    GridConnectionStatus,
    OrganizationKind,
    SiteStatus,
    StationLifecycleStatus,
)


class Organization(TimestampMixin, Base):
    __tablename__ = 'organization'
    __table_args__ = (
        UniqueConstraint('registration_code', name='uq_organization_registration_code'),
        {'schema': 'core'},
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique organization identifier',
    )
    legal_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Official legal name of the organization',
    )
    registration_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='State registration code (UNP, EIN, etc.)',
    )
    organization_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=OrganizationKind.OTHER,
        comment=f'Organization type: {", ".join(OrganizationKind.ALL)}',
    )

    owned_sites: Mapped[list['Site']] = relationship(
        'Site',
        back_populates='land_owner',
        foreign_keys='Site.land_owner_id',
        lazy='select',
    )
    utility_connections: Mapped[list['GridConnection']] = relationship(
        'GridConnection',
        back_populates='utility',
        lazy='select',
    )

    def __repr__(self) -> str:
        return f"Organization(id={self.organization_id}, name='{self.legal_name}')"


class Program(TimestampMixin, Base):
    __tablename__ = 'program'
    __table_args__ = (
        CheckConstraint(
            'period_end IS NULL OR period_start IS NULL OR period_end >= period_start',
            name='ck_program_period_valid',
        ),
        {'schema': 'core'},
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique program identifier',
    )
    program_code: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        comment='Short program code (e.g., "EVN-2024-2030")',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Program name in Russian',
    )
    period_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Program start date',
    )
    period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Program end date',
    )
    approved_budget_byn: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment='Total approved budget in BYN',
    )

    sites: Mapped[list['Site']] = relationship(
        'Site',
        back_populates='program',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f"Program(code='{self.program_code}', name='{self.name_ru}')"


class Site(TimestampMixin, Base):
    __tablename__ = 'site'
    __table_args__ = (
        UniqueConstraint('site_code', name='uq_site_code'),
        CheckConstraint(
            'latitude IS NULL OR (latitude >= -90 AND latitude <= 90)',
            name='ck_site_latitude_valid',
        ),
        CheckConstraint(
            'longitude IS NULL OR (longitude >= -180 AND longitude <= 180)',
            name='ck_site_longitude_valid',
        ),
        CheckConstraint(
            'investment_priority BETWEEN 1 AND 3',
            name='ck_site_investment_priority_valid',
        ),
        CheckConstraint(
            f"site_status IN ({','.join(repr(s) for s in SiteStatus.ALL)})",
            name='ck_site_status_valid',
        ),
        Index('ix_site_region_status', 'region_id', 'site_status'),
        Index('ix_site_program', 'program_id'),
        {'schema': 'core'},
    )

    site_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique site identifier',
    )
    site_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Short site code (e.g., "SITE-067")',
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.program.program_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the development program',
    )
    region_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey('ref.region.region_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the region',
    )
    site_type_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey('ref.site_type.site_type_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to site type (city, highway, mall, etc.)',
    )
    name_ru: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Site name in Russian',
    )
    address_ru: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Full address in Russian',
    )
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
        comment='Latitude coordinate (WGS84)',
    )
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
        comment='Longitude coordinate (WGS84)',
    )
    land_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the land owner organization',
    )
    investment_priority: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment='Investment priority (1=high, 2=medium, 3=low)',
    )
    planned_go_live: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned commercial operation start date',
    )
    actual_go_live: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual commercial operation start date',
    )
    site_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=SiteStatus.PLANNED,
        comment=f'Site lifecycle status: {", ".join(SiteStatus.ALL)}',
    )

    program: Mapped['Program | None'] = relationship(
        'Program',
        back_populates='sites',
        lazy='selectin',
    )
    region: Mapped['Region | None'] = relationship(
        'Region',
        lazy='selectin',
    )
    site_type: Mapped['SiteType | None'] = relationship(
        'SiteType',
        lazy='selectin',
    )
    land_owner: Mapped['Organization | None'] = relationship(
        'Organization',
        back_populates='owned_sites',
        foreign_keys='Site.land_owner_id',
        lazy='selectin',
    )
    charging_stations: Mapped[list['ChargingStation']] = relationship(
        'ChargingStation',
        back_populates='site',
        lazy='select',
        cascade='all, delete-orphan',
    )
    grid_connections: Mapped[list['GridConnection']] = relationship(
        'GridConnection',
        back_populates='site',
        lazy='select',
        cascade='all, delete-orphan',
    )
    capacity_history: Mapped[list['SiteCapacityHistory']] = relationship(
        'SiteCapacityHistory',
        back_populates='site',
        lazy='select',
        order_by='SiteCapacityHistory.valid_from.desc()',
    )

    def __repr__(self) -> str:
        return f"Site(code='{self.site_code}', name='{self.name_ru}', status='{self.site_status}')"

    @property
    def is_operating(self) -> bool:
        return self.site_status == SiteStatus.OPERATING

    @property
    def is_active(self) -> bool:
        return self.site_status not in (SiteStatus.CLOSED, SiteStatus.SUSPENDED)


class GridConnection(TimestampMixin, Base):
    __tablename__ = 'grid_connection'
    __table_args__ = (
        CheckConstraint(
            'requested_power_kw >= 0',
            name='ck_grid_connection_requested_power_valid',
        ),
        CheckConstraint(
            'contracted_power_kw >= 0',
            name='ck_grid_connection_contracted_power_valid',
        ),
        CheckConstraint(
            'approved_power_kw >= 0',
            name='ck_grid_connection_approved_power_valid',
        ),
        Index('ix_grid_site', 'site_id'),
        {'schema': 'core'},
    )

    grid_connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique grid connection identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the site',
    )
    utility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.organization.organization_id', ondelete='SET NULL'),
        nullable=True,
        comment='Reference to the utility organization',
    )
    application_no: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Grid connection application number',
    )
    technical_conditions_no: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Technical conditions number',
    )
    requested_power_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Requested power capacity in kW',
    )
    contracted_power_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Contracted power capacity in kW',
    )
    approved_power_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Approved power capacity in kW',
    )
    planned_energization_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Planned date of energization',
    )
    actual_energization_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Actual date of energization',
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=GridConnectionStatus.REQUESTED,
        comment=f'Grid connection status: {", ".join(GridConnectionStatus.ALL)}',
    )

    site: Mapped['Site'] = relationship(
        'Site',
        back_populates='grid_connections',
        lazy='selectin',
    )
    utility: Mapped['Organization | None'] = relationship(
        'Organization',
        back_populates='grid_connections',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f"GridConnection(id={self.grid_connection_id}, status='{self.status}')"


class ChargingStation(TimestampMixin, Base):
    __tablename__ = 'charging_station'
    __table_args__ = (
        UniqueConstraint('station_code', name='uq_charging_station_code'),
        UniqueConstraint(
            'manufacturer',
            'serial_number',
            name='uq_charging_station_manufacturer_serial',
        ),
        CheckConstraint(
            'rated_total_power_kw > 0',
            name='ck_station_rated_power_positive',
        ),
        CheckConstraint(
            'simultaneous_power_limit_kw IS NULL OR simultaneous_power_limit_kw > 0',
            name='ck_station_simultaneous_power_positive',
        ),
        CheckConstraint(
            'retired_at IS NULL OR commissioned_at IS NULL OR retired_at >= commissioned_at',
            name='ck_station_retired_after_commissioned',
        ),
        Index('ix_station_site_type', 'site_id', 'charger_type_id'),
        {'schema': 'core'},
    )

    station_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique charging station identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the site',
    )
    station_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Station code (e.g., "ST-067-01")',
    )
    charger_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey('ref.charger_type.charger_type_id'),
        nullable=False,
        comment='Reference to charger type (AC, HYBRID, DC, OTHER)',
    )
    manufacturer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Equipment manufacturer name',
    )
    model: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Equipment model name',
    )
    serial_number: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Equipment serial number',
    )
    rated_total_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        comment='Rated total power capacity in kW (passport value)',
    )
    simultaneous_power_limit_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Maximum simultaneous power output in kW (for power sharing)',
    )
    installed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Physical installation date',
    )
    commissioned_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Commissioning date (ready for operation)',
    )
    retired_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Retirement date (decommissioned)',
    )
    lifecycle_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=StationLifecycleStatus.PLANNED,
        comment=f'Station lifecycle status: {", ".join(StationLifecycleStatus.ALL)}',
    )

    site: Mapped['Site'] = relationship(
        'Site',
        back_populates='charging_stations',
        lazy='selectin',
    )
    charger_type: Mapped['ChargerType'] = relationship(
        'ChargerType',
        lazy='selectin',
    )
    evses: Mapped[list['Evse']] = relationship(
        'Evse',
        back_populates='charging_station',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='Evse.position_number',
    )

    def __repr__(self) -> str:
        return f"ChargingStation(code='{self.station_code}', type='{self.charger_type_id}')"

    @property
    def is_operating(self) -> bool:
        return self.lifecycle_status == StationLifecycleStatus.OPERATING

    @property
    def effective_power_kw(self) -> Decimal:
        if self.simultaneous_power_limit_kw is not None:
            return min(self.rated_total_power_kw, self.simultaneous_power_limit_kw)
        return self.rated_total_power_kw


class Evse(TimestampMixin, Base):
    __tablename__ = 'evse'
    __table_args__ = (
        UniqueConstraint('evse_code', name='uq_evse_code'),
        UniqueConstraint(
            'station_id',
            'position_number',
            name='uq_evse_station_position',
        ),
        CheckConstraint(
            'position_number > 0',
            name='ck_evse_position_positive',
        ),
        CheckConstraint(
            'nominal_power_kw > 0',
            name='ck_evse_nominal_power_positive',
        ),
        CheckConstraint(
            f"current_kind IN ({','.join(repr(c) for c in CurrentKind.ALL)})",
            name='ck_evse_current_kind_valid',
        ),
        CheckConstraint(
            'retired_at IS NULL OR commissioned_at IS NULL OR retired_at >= commissioned_at',
            name='ck_evse_retired_after_commissioned',
        ),
        Index('ix_evse_station', 'station_id'),
        {'schema': 'core'},
    )

    evse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique EVSE identifier',
    )
    station_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.charging_station.station_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the charging station',
    )
    evse_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='EVSE code (e.g., "EVSE-067-01-01")',
    )
    position_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Position number within the station (1, 2, 3, ...)',
    )
    nominal_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        comment='Nominal power capacity in kW',
    )
    current_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=f'Current type: {", ".join(CurrentKind.ALL)}',
    )
    commissioned_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Commissioning date',
    )
    retired_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment='Retirement date',
    )
    lifecycle_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=EvseLifecycleStatus.PLANNED,
        comment=f'EVSE lifecycle status: {", ".join(EvseLifecycleStatus.ALL)}',
    )

    charging_station: Mapped['ChargingStation'] = relationship(
        'ChargingStation',
        back_populates='evses',
        lazy='selectin',
    )
    connectors: Mapped[list['Connector']] = relationship(
        'Connector',
        back_populates='evse',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='Connector.connector_no',
    )

    def __repr__(self) -> str:
        return f"Evse(code='{self.evse_code}', position={self.position_number})"

    @property
    def is_operating(self) -> bool:
        return self.lifecycle_status == EvseLifecycleStatus.OPERATING


class Connector(TimestampMixin, Base):
    __tablename__ = 'connector'
    __table_args__ = (
        UniqueConstraint(
            'evse_id',
            'connector_no',
            name='uq_connector_evse_no',
        ),
        CheckConstraint(
            'connector_no > 0',
            name='ck_connector_no_positive',
        ),
        CheckConstraint(
            'rated_power_kw IS NULL OR rated_power_kw > 0',
            name='ck_connector_rated_power_positive',
        ),
        {'schema': 'core'},
    )

    connector_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique connector identifier',
    )
    evse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.evse.evse_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the EVSE',
    )
    connector_no: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment='Connector number within the EVSE (1, 2, 3, ...)',
    )
    connector_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey('ref.connector_type.connector_type_id'),
        nullable=False,
        comment='Reference to connector type (TYPE2, CCS2, CHADEMO, etc.)',
    )
    rated_power_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Rated power capacity in kW',
    )

    evse: Mapped['Evse'] = relationship(
        'Evse',
        back_populates='connectors',
        lazy='select',
    )
    connector_type: Mapped['ConnectorType'] = relationship(
        'ConnectorType',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return f"Connector(evse_id={self.evse_id}, no={self.connector_no}, type_id={self.connector_type_id})"


class SiteCapacityHistory(TimestampMixin, Base):
    __tablename__ = 'site_capacity_history'
    __table_args__ = (
        CheckConstraint(
            'installed_station_power_kw >= 0',
            name='ck_capacity_installed_power_valid',
        ),
        CheckConstraint(
            'simultaneous_power_limit_kw IS NULL OR simultaneous_power_limit_kw >= 0',
            name='ck_capacity_simultaneous_power_valid',
        ),
        CheckConstraint(
            'grid_limit_kw IS NULL OR grid_limit_kw >= 0',
            name='ck_capacity_grid_limit_valid',
        ),
        CheckConstraint(
            'ports_count >= 0',
            name='ck_capacity_ports_count_valid',
        ),
        CheckConstraint(
            'valid_to IS NULL OR valid_to > valid_from',
            name='ck_capacity_valid_period',
        ),
        Index('ix_capacity_site_valid', 'site_id', 'valid_from'),
        {'schema': 'core'},
    )

    site_capacity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment='Unique capacity history record identifier',
    )
    site_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('core.site.site_id', ondelete='CASCADE'),
        nullable=False,
        comment='Reference to the site',
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment='Start of the validity period',
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='End of the validity period (NULL = current record)',
    )
    installed_station_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        comment='Total installed station power in kW',
    )
    simultaneous_power_limit_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Simultaneous power limit in kW (for power sharing)',
    )
    grid_limit_kw: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment='Grid connection power limit in kW',
    )
    ports_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='Number of charging ports (EVSEs)',
    )
    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='Reason for the capacity change',
    )

    site: Mapped['Site'] = relationship(
        'Site',
        back_populates='capacity_history',
        lazy='selectin',
    )

    def __repr__(self) -> str:
        return (
            f"SiteCapacityHistory(site_id={self.site_id}, "
            f"from={self.valid_from}, to={self.valid_to})"
        )

    @property
    def is_current(self) -> bool:
        return self.valid_to is None