from collections.abc import Sequence

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.pm.models import StageExecution
from app.features.reference.models import ProjectStage
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_PROJECT_STAGE_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'stage_no': ProjectStage.stage_no,
    'code': ProjectStage.code,
    'name_ru': ProjectStage.name_ru,
    'is_milestone': ProjectStage.is_milestone,
    'created_at': ProjectStage.created_at,
    'updated_at': ProjectStage.updated_at,
}


class ProjectStageRepository(SQLAlchemyRepository[ProjectStage, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProjectStage, session)

    async def get_by_code(self, code: str) -> ProjectStage | None:
        logger.debug(f'[{self._model.__name__}] Fetching project stage by code: {code}')
        stmt = select(ProjectStage).where(ProjectStage.code == code)
        result = await self._session.execute(stmt)
        project_stage = result.scalar_one_or_none()
        if project_stage:
            logger.debug(
                f'[{self._model.__name__}] Found project stage with code: {code}'
            )
        else:
            logger.debug(
                f'[{self._model.__name__}] Project stage with code {code} not found'
            )
        return project_stage

    async def has_linked_entities(self, stage_no: int) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities for stage_no={stage_no}'
        )
        stmt = select(exists().where(StageExecution.stage_no == stage_no))
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
    ) -> tuple[Sequence[ProjectStage], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing project stages '
            f'(limit={limit}, offset={offset}, sort={sort}, search={search!r})'
        )
        filters: list[ColumnElement[bool]] = []

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        ProjectStage.code.ilike(pattern, escape='\\'),
                        ProjectStage.name_ru.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(ProjectStage).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _PROJECT_STAGE_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )
        items_stmt = (
            select(ProjectStage)
            .where(*filters)
            .order_by(primary_order, ProjectStage.stage_no.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} project stages'
        )
        return items, total_items
