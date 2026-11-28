from types import TracebackType
from typing import Protocol, Self

from app.features.core.repositories.organization import OrganizationRepository
from app.features.reference.repositories.charger_type import ChargerTypeRepository
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


class UnitOfWorkProtocol(Protocol):
    @property
    def charger_types(self) -> ChargerTypeRepository: ...

    @property
    def connector_types(self) -> ConnectorTypeRepository: ...

    @property
    def cost_categories(self) -> CostCategoryRepository: ...

    @property
    def organizations(self) -> OrganizationRepository: ...

    @property
    def project_stages(self) -> ProjectStageRepository: ...

    @property
    def regions(self) -> RegionRepository: ...

    @property
    def site_types(self) -> SiteTypeRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
