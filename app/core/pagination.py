from dataclasses import dataclass
from math import ceil

from pydantic import BaseModel, Field

from app.core.config import settings


class PaginationMeta(BaseModel):
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    current_page: int = Field(ge=1)
    limit: int = Field(ge=1)
    has_more: bool


class PaginatedResponse[ItemT](BaseModel):
    data: list[ItemT]
    meta: PaginationMeta


@dataclass(frozen=True, slots=True)
class PaginationParams:
    page: int
    limit: int
    offset: int


def resolve_limit(requested_limit: int | None) -> int:
    if requested_limit is None:
        return settings.API_PAGINATION_DEFAULT_LIMIT
    return min(requested_limit, settings.API_PAGINATION_MAX_LIMIT)


def build_pagination_params(page: int, requested_limit: int | None) -> PaginationParams:
    limit = resolve_limit(requested_limit)
    offset = (page - 1) * limit
    return PaginationParams(page=page, limit=limit, offset=offset)


def build_pagination_meta(
    *,
    total_items: int,
    page: int,
    limit: int,
) -> PaginationMeta:
    if total_items == 0:
        total_pages = 0
        has_more = False
    else:
        total_pages = ceil(total_items / limit)
        has_more = page < total_pages
    return PaginationMeta(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        limit=limit,
        has_more=has_more,
    )


def build_paginated_response[ItemT](
    items: list[ItemT] | tuple[ItemT, ...],
    *,
    total_items: int,
    page: int,
    limit: int,
) -> PaginatedResponse[ItemT]:
    return PaginatedResponse(
        data=list(items),
        meta=build_pagination_meta(
            total_items=total_items,
            page=page,
            limit=limit,
        ),
    )
