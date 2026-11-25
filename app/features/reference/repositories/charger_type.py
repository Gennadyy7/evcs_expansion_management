from collections.abc import Sequence

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.core.models import ChargingStation
from app.features.pm.models import NetworkPlanLine, ProjectScope
from app.features.reference.models import ChargerType
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_CHARGER_TYPE_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'charger_type_id': ChargerType.charger_type_id,
    'code': ChargerType.code,
    'name_ru': ChargerType.name_ru,
    'created_at': ChargerType.created_at,
    'updated_at': ChargerType.updated_at,
}


class ChargerTypeRepository(SQLAlchemyRepository[ChargerType, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ChargerType, session)

    async def get_by_code(self, code: str) -> ChargerType | None:
        logger.debug(f'[{self._model.__name__}] Fetching charger type by code: {code}')
        stmt = select(ChargerType).where(ChargerType.code == code)
        result = await self._session.execute(stmt)
        charger_type = result.scalar_one_or_none()
        if charger_type:
            logger.debug(
                f'[{self._model.__name__}] Found charger type with code: {code}'
            )
        else:
            logger.debug(
                f'[{self._model.__name__}] Charger type with code {code} not found'
            )
        return charger_type

    async def has_linked_entities(self, charger_type_id: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities '
            f'for charger_type_id={charger_type_id}'
        )
        station_stmt = select(
            exists().where(ChargingStation.charger_type_id == charger_type_id)
        )
        station_result = await self._session.execute(station_stmt)
        if bool(station_result.scalar()):
            return True

        plan_line_stmt = select(
            exists().where(NetworkPlanLine.charger_type_id == charger_type_id)
        )
        plan_line_result = await self._session.execute(plan_line_stmt)
        if bool(plan_line_result.scalar()):
            return True

        scope_stmt = select(
            exists().where(ProjectScope.charger_type_id == charger_type_id)
        )
        scope_result = await self._session.execute(scope_stmt)
        return bool(scope_result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
    ) -> tuple[Sequence[ChargerType], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing charger types '
            f'(limit={limit}, offset={offset}, sort={sort}, search={search!r})'
        )
        filters: list[ColumnElement[bool]] = []

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        ChargerType.code.ilike(pattern, escape='\\'),
                        ChargerType.name_ru.ilike(pattern, escape='\\'),
                        ChargerType.description.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(ChargerType).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _CHARGER_TYPE_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )
        items_stmt = (
            select(ChargerType)
            .where(*filters)
            .order_by(primary_order, ChargerType.charger_type_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} charger types'
        )
        return items, total_items
