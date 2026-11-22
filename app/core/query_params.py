from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status

from app.core.constants import CoreErrorCode
from app.core.messages import get_message

SortOrder = Literal['asc', 'desc']


@dataclass(frozen=True, slots=True)
class SortParams:
    sort_by: str
    sort_order: SortOrder


def resolve_sort_params(
    *,
    sort_by: str | None,
    sort_order: str | None,
    allowed_columns: frozenset[str],
    default_sort_by: str,
    default_sort_order: SortOrder = 'desc',
) -> SortParams:
    resolved_sort_by = sort_by if sort_by is not None else default_sort_by
    if resolved_sort_by not in allowed_columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                'code': CoreErrorCode.INVALID_SORT_BY,
                'message': get_message(CoreErrorCode.INVALID_SORT_BY),
                'sort_by': resolved_sort_by,
                'allowed': sorted(allowed_columns),
            },
        )

    resolved_sort_order: SortOrder
    if sort_order is None:
        resolved_sort_order = default_sort_order
    elif sort_order not in {'asc', 'desc'}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                'code': CoreErrorCode.INVALID_SORT_ORDER,
                'message': get_message(CoreErrorCode.INVALID_SORT_ORDER),
                'sort_order': sort_order,
                'allowed': ['asc', 'desc'],
            },
        )
    elif sort_order == 'asc':
        resolved_sort_order = 'asc'
    else:
        resolved_sort_order = 'desc'

    return SortParams(
        sort_by=resolved_sort_by,
        sort_order=resolved_sort_order,
    )
