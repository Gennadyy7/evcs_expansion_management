from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import CostCategory

logger = get_logger(__name__)


class CostCategoryRepository(SQLAlchemyRepository[CostCategory, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CostCategory, session)

    async def get_by_kind_and_code(
        self, cost_kind: str, code: str
    ) -> CostCategory | None:
        logger.debug(
            f'[CostCategory] Fetching cost category by kind={cost_kind}, code={code}'
        )
        stmt = select(CostCategory).where(
            CostCategory.cost_kind == cost_kind, CostCategory.code == code
        )
        result = await self._session.execute(stmt)
        cost_category = result.scalar_one_or_none()
        if cost_category:
            logger.debug(
                f'[CostCategory] Found cost category: kind={cost_kind}, code={code}'
            )
        else:
            logger.debug(
                f'[CostCategory] Cost category not found: kind={cost_kind}, code={code}'
            )
        return cost_category

    async def get_by_kind(self, cost_kind: str) -> list[CostCategory]:
        logger.debug(
            f'[CostCategory] Fetching all cost categories for kind={cost_kind}'
        )
        stmt = select(CostCategory).where(CostCategory.cost_kind == cost_kind)
        result = await self._session.execute(stmt)
        categories = list(result.scalars().all())
        logger.debug(
            f'[CostCategory] Retrieved {len(categories)} cost categories for kind={cost_kind}'
        )
        return categories
