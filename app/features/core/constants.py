from enum import StrEnum


class SiteStatus(StrEnum):
    CANDIDATE = 'CANDIDATE'
    PLANNED = 'PLANNED'
    IN_PROGRESS = 'IN_PROGRESS'
    BLOCKED = 'BLOCKED'
    COMMISSIONED = 'COMMISSIONED'
    OPERATING = 'OPERATING'
    SUSPENDED = 'SUSPENDED'
    CLOSED = 'CLOSED'


class StationLifecycleStatus(StrEnum):
    PLANNED = 'PLANNED'
    INSTALLED = 'INSTALLED'
    COMMISSIONED = 'COMMISSIONED'
    OPERATING = 'OPERATING'
    RETIRED = 'RETIRED'


class EvseLifecycleStatus(StrEnum):
    PLANNED = 'PLANNED'
    INSTALLED = 'INSTALLED'
    COMMISSIONED = 'COMMISSIONED'
    OPERATING = 'OPERATING'
    RETIRED = 'RETIRED'


class GridConnectionStatus(StrEnum):
    REQUESTED = 'REQUESTED'
    APPROVED = 'APPROVED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'


class OrganizationKind(StrEnum):
    OWNER = 'owner'
    CONTRACTOR = 'contractor'
    VENDOR = 'vendor'
    UTILITY = 'utility'
    OTHER = 'other'


class CurrentKind(StrEnum):
    AC = 'AC'
    DC = 'DC'
