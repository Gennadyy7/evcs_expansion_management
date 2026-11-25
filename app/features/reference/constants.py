from enum import StrEnum

from app.core.query_params import SortOrder


class CostKind(StrEnum):
    CAPEX = 'CAPEX'
    OPEX = 'OPEX'


class ReferenceErrorCode(StrEnum):
    REGION_NOT_FOUND = 'REGION_NOT_FOUND'
    REGION_CODE_ALREADY_EXISTS = 'REGION_CODE_ALREADY_EXISTS'
    REGION_PARENT_NOT_FOUND = 'REGION_PARENT_NOT_FOUND'
    REGION_SELF_PARENT = 'REGION_SELF_PARENT'
    REGION_CYCLE_DETECTED = 'REGION_CYCLE_DETECTED'
    REGION_HAS_CHILDREN = 'REGION_HAS_CHILDREN'
    REGION_IN_USE = 'REGION_IN_USE'

    CHARGER_TYPE_NOT_FOUND = 'CHARGER_TYPE_NOT_FOUND'
    CHARGER_TYPE_CODE_ALREADY_EXISTS = 'CHARGER_TYPE_CODE_ALREADY_EXISTS'
    CHARGER_TYPE_IN_USE = 'CHARGER_TYPE_IN_USE'


REGION_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'region_id',
        'code',
        'name_ru',
        'created_at',
        'updated_at',
    }
)
REGION_DEFAULT_SORT_BY: str = 'code'
REGION_DEFAULT_SORT_ORDER: SortOrder = 'asc'
REGION_TREE_DEFAULT_DEPTH: int = 2
REGION_TREE_MAX_DEPTH: int = 5

CHARGER_TYPE_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'charger_type_id',
        'code',
        'name_ru',
        'created_at',
        'updated_at',
    }
)
CHARGER_TYPE_DEFAULT_SORT_BY: str = 'code'
CHARGER_TYPE_DEFAULT_SORT_ORDER: SortOrder = 'asc'
