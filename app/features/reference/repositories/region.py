from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import Region

logger = get_logger(__name__)


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

    async def get_all_with_children(self, limit: int, offset: int) -> Sequence[Region]:
        logger.debug(
            f'[{self._model.__name__}] Fetching all regions with children (limit={limit}, offset={offset})'
        )
        stmt = (
            select(Region)
            .options(selectinload(Region.children))
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        regions = list(result.scalars().all())
        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(regions)} regions with children'
        )
        return regions

    async def get_root_regions(self) -> Sequence[Region]:
        logger.debug(f'[{self._model.__name__}] Fetching root regions')
        stmt = select(Region).where(Region.parent_region_id.is_(None))
        result = await self._session.execute(stmt)
        regions = list(result.scalars().all())
        logger.debug(f'[{self._model.__name__}] Retrieved {len(regions)} root regions')
        return regions
