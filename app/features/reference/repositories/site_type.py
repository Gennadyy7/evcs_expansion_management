from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import SiteType

logger = get_logger(__name__)


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
