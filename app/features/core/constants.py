from enum import StrEnum

from app.core.query_params import SortOrder


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


class CoreErrorCode(StrEnum):
    ORGANIZATION_NOT_FOUND = 'ORGANIZATION_NOT_FOUND'
    ORGANIZATION_REGISTRATION_CODE_EXISTS = 'ORGANIZATION_REGISTRATION_CODE_EXISTS'
    ORGANIZATION_IN_USE = 'ORGANIZATION_IN_USE'


ORGANIZATION_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'organization_id',
        'legal_name',
        'registration_code',
        'organization_kind',
        'created_at',
        'updated_at',
    }
)
ORGANIZATION_DEFAULT_SORT_BY: str = 'legal_name'
ORGANIZATION_DEFAULT_SORT_ORDER: SortOrder = 'asc'
