from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
