from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.core.unit_of_work.protocol import UnitOfWorkProtocol
from app.features.core.repositories.organization import OrganizationRepository
from app.features.reference.repositories.charger_type import (
    ChargerTypeRepository,
)
from app.features.reference.repositories.connector_type import (
    ConnectorTypeRepository,
)
from app.features.reference.repositories.cost_category import (
    CostCategoryRepository,
)
from app.features.reference.repositories.project_stage import (
    ProjectStageRepository,
)
from app.features.reference.repositories.region import RegionRepository
from app.features.reference.repositories.site_type import SiteTypeRepository

logger = get_logger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWorkProtocol):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._organizations: OrganizationRepository | None = None
        self._charger_types: ChargerTypeRepository | None = None
        self._connector_types: ConnectorTypeRepository | None = None
        self._cost_categories: CostCategoryRepository | None = None
        self._project_stages: ProjectStageRepository | None = None
        self._regions: RegionRepository | None = None
        self._site_types: SiteTypeRepository | None = None
        self._committed = False
        logger.debug('SQLAlchemyUnitOfWork initialized with session factory')

    @property
    def organizations(self) -> OrganizationRepository:
        if self._organizations is None:
            logger.error(
                'Attempted to access organizations repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._organizations

    @property
    def charger_types(self) -> ChargerTypeRepository:
        if self._charger_types is None:
            logger.error(
                'Attempted to access charger_types repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._charger_types

    @property
    def connector_types(self) -> ConnectorTypeRepository:
        if self._connector_types is None:
            logger.error(
                'Attempted to access connector_types repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._connector_types

    @property
    def cost_categories(self) -> CostCategoryRepository:
        if self._cost_categories is None:
            logger.error(
                'Attempted to access cost_categories repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._cost_categories

    @property
    def project_stages(self) -> ProjectStageRepository:
        if self._project_stages is None:
            logger.error(
                'Attempted to access project_stages repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._project_stages

    @property
    def regions(self) -> RegionRepository:
        if self._regions is None:
            logger.error(
                'Attempted to access regions repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._regions

    @property
    def site_types(self) -> SiteTypeRepository:
        if self._site_types is None:
            logger.error(
                'Attempted to access site_types repository '
                'outside of context manager block'
            )
            raise RuntimeError(
                'UnitOfWork context is not active. '
                'Access attributes inside an "async with" block.'
            )
        return self._site_types

    async def __aenter__(self) -> Self:
        logger.debug('Entering UnitOfWork context: opening new database session')
        self._session = self._session_factory()
        assert self._session is not None
        logger.debug(
            f'Database session opened successfully. '
            f'Session ID: {hex(id(self._session))}'
        )

        self._organizations = OrganizationRepository(self._session)
        self._charger_types = ChargerTypeRepository(self._session)
        self._connector_types = ConnectorTypeRepository(self._session)
        self._cost_categories = CostCategoryRepository(self._session)
        self._project_stages = ProjectStageRepository(self._session)
        self._regions = RegionRepository(self._session)
        self._site_types = SiteTypeRepository(self._session)
        self._committed = False
        logger.debug('Repositories initialized for UnitOfWork session')
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        session_id = hex(id(self._session)) if self._session else 'None'
        logger.debug(f'Exiting UnitOfWork context for Session ID: {session_id}')
        try:
            if exc_type is not None:
                logger.warning(
                    f'Exception detected inside UnitOfWork '
                    f'[Session ID: {session_id}]. '
                    f'Type: {exc_type.__name__}, Value: {exc_val}. '
                    'Triggering rollback.'
                )
                await self.rollback()
            elif not self._committed:
                logger.debug(
                    f'UnitOfWork exiting without commit '
                    f'for Session ID: {session_id}. Triggering rollback.'
                )
                await self.rollback()
        finally:
            assert self._session is not None
            logger.debug(f'Closing database session. Session ID: {session_id}')
            await self._session.close()
            logger.debug(f'Database session closed. Session ID: {session_id}')

    async def commit(self) -> None:
        if self._session:
            session_id = hex(id(self._session))
            logger.debug(f'Executing SQL COMMIT for Session ID: {session_id}')
            await self._session.commit()
            self._committed = True
            logger.debug(
                f'SQL COMMIT executed successfully for Session ID: {session_id}'
            )
        else:
            logger.warning('Commit attempted on a missing or inactive session')

    async def rollback(self) -> None:
        if self._session:
            session_id = hex(id(self._session))
            logger.debug(f'Executing SQL ROLLBACK for Session ID: {session_id}')
            await self._session.rollback()
            logger.debug(
                f'SQL ROLLBACK executed successfully for Session ID: {session_id}'
            )
        else:
            logger.warning('Rollback attempted on a missing or inactive session')
