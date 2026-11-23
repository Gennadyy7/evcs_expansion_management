from enum import StrEnum

from app.core.query_params import SortOrder


class ReferenceErrorCode(StrEnum):
    REGION_NOT_FOUND = 'REGION_NOT_FOUND'
    REGION_CODE_ALREADY_EXISTS = 'REGION_CODE_ALREADY_EXISTS'
    REGION_PARENT_NOT_FOUND = 'REGION_PARENT_NOT_FOUND'
    REGION_SELF_PARENT = 'REGION_SELF_PARENT'
    REGION_CYCLE_DETECTED = 'REGION_CYCLE_DETECTED'
    REGION_HAS_CHILDREN = 'REGION_HAS_CHILDREN'
    REGION_IN_USE = 'REGION_IN_USE'


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
