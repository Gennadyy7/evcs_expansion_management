from enum import StrEnum


class RevisionStatus(StrEnum):
    DRAFT = 'DRAFT'
    APPROVED = 'APPROVED'
    SUPERSEDED = 'SUPERSEDED'


class RevenueEntryType(StrEnum):
    CHARGE = 'CHARGE'
    REFUND = 'REFUND'
    ADJUSTMENT = 'ADJUSTMENT'
