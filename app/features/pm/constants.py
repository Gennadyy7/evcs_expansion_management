from enum import StrEnum


class ProjectType(StrEnum):
    NEW_BUILD = 'NEW_BUILD'
    EXPANSION = 'EXPANSION'
    UPGRADE = 'UPGRADE'
    RELOCATION = 'RELOCATION'
    REPLACEMENT = 'REPLACEMENT'


class ProjectStatus(StrEnum):
    PLANNED = 'PLANNED'
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'
    ON_HOLD = 'ON_HOLD'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'


class ApprovalStatus(StrEnum):
    DRAFT = 'DRAFT'
    APPROVED = 'APPROVED'
    SUPERSEDED = 'SUPERSEDED'


class PlanScenario(StrEnum):
    BASE = 'BASE'
    OPTIMISTIC = 'OPTIMISTIC'
    PESSIMISTIC = 'PESSIMISTIC'
