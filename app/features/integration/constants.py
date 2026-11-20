from enum import StrEnum


class SourceSystemKind(StrEnum):
    CPMS = 'CPMS'
    ERP = 'ERP'
    BILLING = 'BILLING'
    EDMS = 'EDMS'
    GIS = 'GIS'
    CRM = 'CRM'
    # OTHER = 'OTHER'


class EntityKind(StrEnum):
    SITE = 'SITE'
    STATION = 'STATION'
    EVSE = 'EVSE'
    CONNECTOR = 'CONNECTOR'


class IngestionBatchStatus(StrEnum):
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    PARTIAL = 'PARTIAL'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class InboxEventStatus(StrEnum):
    NEW = 'NEW'
    PROCESSING = 'PROCESSING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'
    SKIPPED = 'SKIPPED'
