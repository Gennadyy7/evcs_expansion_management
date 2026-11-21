from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import ConnectorType

logger = get_logger(__name__)


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
