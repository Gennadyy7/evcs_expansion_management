"""User-facing Russian API messages.

Russian copy for API responses lives in MESSAGES only.
"""

from app.core.constants import CoreErrorCode

CORE_MESSAGES: dict[str, str] = {
    CoreErrorCode.INVALID_SORT_BY: 'Недопустимое поле сортировки',
    CoreErrorCode.INVALID_SORT_ORDER: (
        'Недопустимый порядок сортировки. Допустимые значения: asc, desc'
    ),
}


def get_message(code: str) -> str:
    return CORE_MESSAGES.get(code, code)
