from enum import StrEnum


class ChargingSessionStatus(StrEnum):
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    ABORTED = 'ABORTED'
    FAILED = 'FAILED'


class Severity(StrEnum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
