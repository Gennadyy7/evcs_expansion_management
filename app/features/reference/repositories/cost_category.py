from collections.abc import Sequence

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.finance.models import (
    CapexActual,
    CapexBudget,
    CapexCommitment,
    CapexForecastEac,
    OpexEntry,
)
from app.features.reference.constants import CostKind
from app.features.reference.models import CostCategory
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_COST_CATEGORY_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'category_id': CostCategory.category_id,
    'cost_kind': CostCategory.cost_kind,
    'code': CostCategory.code,
    'name_ru': CostCategory.name_ru,
    'created_at': CostCategory.created_at,
    'updated_at': CostCategory.updated_at,
}


class CostCategoryRepository(SQLAlchemyRepository[CostCategory, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CostCategory, session)

    async def get_by_kind_and_code(
        self, cost_kind: CostKind, code: str
    ) -> CostCategory | None:
        logger.debug(
            f'[{self._model.__name__}] Fetching cost category '
            f'by kind={cost_kind}, code={code}'
        )
        stmt = select(CostCategory).where(
            CostCategory.cost_kind == cost_kind, CostCategory.code == code
        )
        result = await self._session.execute(stmt)
        cost_category = result.scalar_one_or_none()
        if cost_category:
            logger.debug(
                f'[{self._model.__name__}] Found cost category: '
                f'kind={cost_kind}, code={code}'
            )
        else:
            logger.debug(
                f'[{self._model.__name__}] Cost category not found: '
                f'kind={cost_kind}, code={code}'
            )
        return cost_category

    async def get_by_kind(self, cost_kind: CostKind) -> Sequence[CostCategory]:
        logger.debug(
            f'[{self._model.__name__}] Fetching all cost categories '
            f'for kind={cost_kind}'
        )
        stmt = select(CostCategory).where(CostCategory.cost_kind == cost_kind)
        result = await self._session.execute(stmt)
        categories = list(result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(categories)} '
            f'cost categories for kind={cost_kind}'
        )
        return categories

    async def has_linked_entities(self, category_id: int, cost_kind: str) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities '
            f'for category_id={category_id}, cost_kind={cost_kind}'
        )
        budget_stmt = select(
            exists().where(
                CapexBudget.category_id == category_id,
                CapexBudget.cost_kind == cost_kind,
            )
        )
        budget_result = await self._session.execute(budget_stmt)
        if bool(budget_result.scalar()):
            return True

        actual_stmt = select(
            exists().where(
                CapexActual.category_id == category_id,
                CapexActual.cost_kind == cost_kind,
            )
        )
        actual_result = await self._session.execute(actual_stmt)
        if bool(actual_result.scalar()):
            return True

        commitment_stmt = select(
            exists().where(
                CapexCommitment.category_id == category_id,
                CapexCommitment.cost_kind == cost_kind,
            )
        )
        commitment_result = await self._session.execute(commitment_stmt)
        if bool(commitment_result.scalar()):
            return True

        forecast_stmt = select(
            exists().where(
                CapexForecastEac.category_id == category_id,
                CapexForecastEac.cost_kind == cost_kind,
            )
        )
        forecast_result = await self._session.execute(forecast_stmt)
        if bool(forecast_result.scalar()):
            return True

        opex_stmt = select(
            exists().where(
                OpexEntry.category_id == category_id,
                OpexEntry.cost_kind == cost_kind,
            )
        )
        opex_result = await self._session.execute(opex_stmt)
        return bool(opex_result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
        cost_kind: CostKind | None = None,
    ) -> tuple[Sequence[CostCategory], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing cost categories '
            f'(limit={limit}, offset={offset}, sort={sort}, '
            f'search={search!r}, cost_kind={cost_kind})'
        )
        filters: list[ColumnElement[bool]] = []

        if cost_kind is not None:
            filters.append(CostCategory.cost_kind == cost_kind)

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        CostCategory.code.ilike(pattern, escape='\\'),
                        CostCategory.name_ru.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(CostCategory).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _COST_CATEGORY_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )
        items_stmt = (
            select(CostCategory)
            .where(*filters)
            .order_by(primary_order, CostCategory.category_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} cost categories'
        )
        return items, total_items
