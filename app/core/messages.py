"""User-facing Russian API messages.

Russian copy for API responses lives in MESSAGES only.
"""

from app.core.constants import QueryParamErrorCode

QUERY_PARAM_MESSAGES: dict[str, str] = {
    QueryParamErrorCode.INVALID_SORT_BY: 'Недопустимое поле сортировки',
    QueryParamErrorCode.INVALID_SORT_ORDER: (
        'Недопустимый порядок сортировки. Допустимые значения: asc, desc'
    ),
}


def get_message(code: str) -> str:
    return QUERY_PARAM_MESSAGES.get(code, code)
