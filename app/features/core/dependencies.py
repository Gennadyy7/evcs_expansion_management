from typing import Annotated

from fastapi import Depends

from app.core.dependencies import UnitOfWorkDep
from app.features.core.services.organization_service import (
    OrganizationService,
)


def get_organization_service(uow: UnitOfWorkDep) -> OrganizationService:
    return OrganizationService(uow)


OrganizationServiceDep = Annotated[
    OrganizationService, Depends(get_organization_service)
]
