from collections.abc import Sequence

from sqlalchemy import (
    ColumnElement,
    UnaryExpression,
    exists,
    func,
    literal,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.core.models import Site
from app.features.pm.models import NetworkPlanLine
from app.features.reference.models import Region

logger = get_logger(__name__)

_REGION_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'region_id': Region.region_id,
    'code': Region.code,
    'name_ru': Region.name_ru,
    'created_at': Region.created_at,
    'updated_at': Region.updated_at,
}


def _escape_like_pattern(value: str) -> str:
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class RegionRepository(SQLAlchemyRepository[Region, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Region, session)

    async def get_by_code(self, code: str) -> Region | None:
        logger.debug(f'[{self._model.__name__}] Fetching region by code: {code}')
        stmt = select(Region).where(Region.code == code)
        result = await self._session.execute(stmt)
        region = result.scalar_one_or_none()
        if region:
            logger.debug(f'[{self._model.__name__}] Found region with code: {code}')
        else:
            logger.debug(f'[{self._model.__name__}] Region with code {code} not found')
        return region

    async def has_children(self, region_id: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking child regions for region_id={region_id}'
        )
        stmt = select(exists().where(Region.parent_region_id == region_id))
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def has_linked_entities(self, region_id: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities for region_id={region_id}'
        )
        site_exists_stmt = select(exists().where(Site.region_id == region_id))
        site_result = await self._session.execute(site_exists_stmt)
        if bool(site_result.scalar()):
            return True

        plan_line_exists_stmt = select(
            exists().where(NetworkPlanLine.region_id == region_id)
        )
        plan_line_result = await self._session.execute(plan_line_exists_stmt)
        return bool(plan_line_result.scalar())

    async def is_descendant(
        self,
        region_id: int,
        potential_descendant_id: int,
    ) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking if region_id={potential_descendant_id} '
            f'is a descendant of region_id={region_id}'
        )
        ancestors_cte = (
            select(
                Region.region_id,
                Region.parent_region_id,
            )
            .where(Region.region_id == potential_descendant_id)
            .cte(name='region_ancestors', recursive=True)
        )
        parent_alias = select(
            Region.region_id,
            Region.parent_region_id,
        ).join(
            ancestors_cte,
            Region.region_id == ancestors_cte.c.parent_region_id,
        )
        ancestors_cte = ancestors_cte.union_all(parent_alias)

        stmt = select(
            exists().where(
                ancestors_cte.c.region_id == region_id,
                literal(potential_descendant_id) != region_id,
            )
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        parent_region_id: int | None = None,
        root_only: bool = False,
        search: str | None = None,
    ) -> tuple[Sequence[Region], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing regions '
            f'(limit={limit}, offset={offset}, sort={sort}, '
            f'parent_region_id={parent_region_id}, root_only={root_only}, search={search!r})'
        )
        filters: list[ColumnElement[bool]] = []
        if root_only:
            filters.append(Region.parent_region_id.is_(None))
        elif parent_region_id is not None:
            filters.append(Region.parent_region_id == parent_region_id)

        if search is not None:
            escaped = _escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        Region.code.ilike(pattern, escape='\\'),
                        Region.name_ru.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(Region).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _REGION_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )

        items_stmt = (
            select(Region)
            .where(*filters)
            .order_by(primary_order, Region.region_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} of {total_items} regions'
        )
        return items, total_items

    async def get_region_with_tree(
        self,
        region_id: int,
        depth: int,
    ) -> Region | None:
        logger.debug(
            f'[{self._model.__name__}] Fetching region {region_id} with tree (depth={depth})'
        )
        stmt = (
            select(Region)
            .where(Region.region_id == region_id)
            .options(Region.tree_loader(depth=depth))
            .order_by(Region.code)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        region = result.scalar_one_or_none()
        if region:
            logger.debug(f'[{self._model.__name__}] Found region {region_id} with tree')
        else:
            logger.debug(f'[{self._model.__name__}] Region {region_id} not found')
        return region

    async def get_root_regions_with_tree(self, depth: int) -> Sequence[Region]:
        logger.debug(
            f'[{self._model.__name__}] Fetching root regions with tree (depth={depth})'
        )
        stmt = (
            select(Region)
            .where(Region.parent_region_id.is_(None))
            .options(Region.tree_loader(depth=depth))
            .order_by(Region.code)
        )
        result = await self._session.execute(stmt)
        regions = list(result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(regions)} root regions with tree'
        )
        return regions
