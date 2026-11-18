from enum import StrEnum


class RevisionStatus(StrEnum):
    DRAFT = 'DRAFT'
    APPROVED = 'APPROVED'
    SUPERSEDED = 'SUPERSEDED'


class CostKind(StrEnum):
    CAPEX = 'CAPEX'
    OPEX = 'OPEX'


class RevenueEntryType(StrEnum):
    CHARGE = 'CHARGE'
    REFUND = 'REFUND'
    ADJUSTMENT = 'ADJUSTMENT'
