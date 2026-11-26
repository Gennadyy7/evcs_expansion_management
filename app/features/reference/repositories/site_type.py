from collections.abc import Sequence

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.core.models import Site
from app.features.reference.models import SiteType
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_SITE_TYPE_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'site_type_id': SiteType.site_type_id,
    'code': SiteType.code,
    'name_ru': SiteType.name_ru,
    'created_at': SiteType.created_at,
    'updated_at': SiteType.updated_at,
}


class SiteTypeRepository(SQLAlchemyRepository[SiteType, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SiteType, session)

    async def get_by_code(self, code: str) -> SiteType | None:
        logger.debug(f'[{self._model.__name__}] Fetching site type by code: {code}')
        stmt = select(SiteType).where(SiteType.code == code)
        result = await self._session.execute(stmt)
        site_type = result.scalar_one_or_none()
        if site_type:
            logger.debug(f'[{self._model.__name__}] Found site type with code: {code}')
        else:
            logger.debug(
                f'[{self._model.__name__}] Site type with code {code} not found'
            )
        return site_type

    async def has_linked_entities(self, site_type_id: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities '
            f'for site_type_id={site_type_id}'
        )
        site_stmt = select(exists().where(Site.site_type_id == site_type_id))
        site_result = await self._session.execute(site_stmt)
        return bool(site_result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
    ) -> tuple[Sequence[SiteType], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing site types '
            f'(limit={limit}, offset={offset}, sort={sort}, search={search!r})'
        )
        filters: list[ColumnElement[bool]] = []

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        SiteType.code.ilike(pattern, escape='\\'),
                        SiteType.name_ru.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(SiteType).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _SITE_TYPE_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )
        items_stmt = (
            select(SiteType)
            .where(*filters)
            .order_by(primary_order, SiteType.site_type_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} site types'
        )
        return items, total_items
