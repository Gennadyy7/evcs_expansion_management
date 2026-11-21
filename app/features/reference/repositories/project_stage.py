from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.reference.models import ProjectStage

logger = get_logger(__name__)


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
