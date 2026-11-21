from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import ChargerType

logger = get_logger(__name__)


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
