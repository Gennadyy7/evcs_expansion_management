from typing import Annotated

from fastapi import Depends

from app.core.dependencies import UnitOfWorkDep
from app.features.reference.services.region_service import RegionService


def get_region_service(uow: UnitOfWorkDep) -> RegionService:
    return RegionService(uow)


RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]
