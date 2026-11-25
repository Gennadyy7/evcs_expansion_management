from collections.abc import Sequence

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.core.models import Connector
from app.features.reference.models import ConnectorType
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_CONNECTOR_TYPE_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'connector_type_id': ConnectorType.connector_type_id,
    'code': ConnectorType.code,
    'name_ru': ConnectorType.name_ru,
    'created_at': ConnectorType.created_at,
    'updated_at': ConnectorType.updated_at,
}


class ConnectorTypeRepository(SQLAlchemyRepository[ConnectorType, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ConnectorType, session)

    async def get_by_code(self, code: str) -> ConnectorType | None:
        logger.debug(
            f'[{self._model.__name__}] Fetching connector type by code: {code}'
        )
        stmt = select(ConnectorType).where(ConnectorType.code == code)
        result = await self._session.execute(stmt)
        connector_type = result.scalar_one_or_none()
        if connector_type:
            logger.debug(
                f'[{self._model.__name__}] Found connector type with code: {code}'
            )
        else:
            logger.debug(
                f'[{self._model.__name__}] Connector type with code {code} not found'
            )
        return connector_type

    async def has_linked_entities(self, connector_type_id: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities '
            f'for connector_type_id={connector_type_id}'
        )
        connector_stmt = select(
            exists().where(Connector.connector_type_id == connector_type_id)
        )
        connector_result = await self._session.execute(connector_stmt)
        return bool(connector_result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
    ) -> tuple[Sequence[ConnectorType], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing connector types '
            f'(limit={limit}, offset={offset}, sort={sort}, search={search!r})'
        )
        filters: list[ColumnElement[bool]] = []

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        ConnectorType.code.ilike(pattern, escape='\\'),
                        ConnectorType.name_ru.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(ConnectorType).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _CONNECTOR_TYPE_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )
        items_stmt = (
            select(ConnectorType)
            .where(*filters)
            .order_by(primary_order, ConnectorType.connector_type_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} connector types'
        )
        return items, total_items
