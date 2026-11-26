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

    CONNECTOR_TYPE_NOT_FOUND = 'CONNECTOR_TYPE_NOT_FOUND'
    CONNECTOR_TYPE_CODE_ALREADY_EXISTS = 'CONNECTOR_TYPE_CODE_ALREADY_EXISTS'
    CONNECTOR_TYPE_IN_USE = 'CONNECTOR_TYPE_IN_USE'

    SITE_TYPE_NOT_FOUND = 'SITE_TYPE_NOT_FOUND'
    SITE_TYPE_CODE_ALREADY_EXISTS = 'SITE_TYPE_CODE_ALREADY_EXISTS'
    SITE_TYPE_IN_USE = 'SITE_TYPE_IN_USE'

    COST_CATEGORY_NOT_FOUND = 'COST_CATEGORY_NOT_FOUND'
    COST_CATEGORY_ALREADY_EXISTS = 'COST_CATEGORY_ALREADY_EXISTS'
    COST_CATEGORY_IN_USE = 'COST_CATEGORY_IN_USE'

    PROJECT_STAGE_NOT_FOUND = 'PROJECT_STAGE_NOT_FOUND'
    PROJECT_STAGE_ALREADY_EXISTS = 'PROJECT_STAGE_ALREADY_EXISTS'
    PROJECT_STAGE_CODE_ALREADY_EXISTS = 'PROJECT_STAGE_CODE_ALREADY_EXISTS'
    PROJECT_STAGE_IN_USE = 'PROJECT_STAGE_IN_USE'


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

CONNECTOR_TYPE_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'connector_type_id',
        'code',
        'name_ru',
        'created_at',
        'updated_at',
    }
)
CONNECTOR_TYPE_DEFAULT_SORT_BY: str = 'code'
CONNECTOR_TYPE_DEFAULT_SORT_ORDER: SortOrder = 'asc'

SITE_TYPE_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'site_type_id',
        'code',
        'name_ru',
        'created_at',
        'updated_at',
    }
)
SITE_TYPE_DEFAULT_SORT_BY: str = 'code'
SITE_TYPE_DEFAULT_SORT_ORDER: SortOrder = 'asc'

COST_CATEGORY_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'category_id',
        'cost_kind',
        'code',
        'name_ru',
        'created_at',
        'updated_at',
    }
)
COST_CATEGORY_DEFAULT_SORT_BY: str = 'cost_kind'
COST_CATEGORY_DEFAULT_SORT_ORDER: SortOrder = 'asc'

PROJECT_STAGE_ALLOWED_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        'stage_no',
        'code',
        'name_ru',
        'is_milestone',
        'created_at',
        'updated_at',
    }
)
PROJECT_STAGE_DEFAULT_SORT_BY: str = 'stage_no'
PROJECT_STAGE_DEFAULT_SORT_ORDER: SortOrder = 'asc'
