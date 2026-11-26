from typing import Annotated

from fastapi import Depends

from app.core.dependencies import UnitOfWorkDep
from app.features.reference.services.charger_type_service import ChargerTypeService
from app.features.reference.services.connector_type_service import ConnectorTypeService
from app.features.reference.services.cost_category_service import CostCategoryService
from app.features.reference.services.project_stage_service import ProjectStageService
from app.features.reference.services.region_service import RegionService
from app.features.reference.services.site_type_service import SiteTypeService


def get_region_service(uow: UnitOfWorkDep) -> RegionService:
    return RegionService(uow)


RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]


def get_charger_type_service(uow: UnitOfWorkDep) -> ChargerTypeService:
    return ChargerTypeService(uow)


ChargerTypeServiceDep = Annotated[ChargerTypeService, Depends(get_charger_type_service)]


def get_connector_type_service(uow: UnitOfWorkDep) -> ConnectorTypeService:
    return ConnectorTypeService(uow)


ConnectorTypeServiceDep = Annotated[
    ConnectorTypeService, Depends(get_connector_type_service)
]


def get_site_type_service(uow: UnitOfWorkDep) -> SiteTypeService:
    return SiteTypeService(uow)


SiteTypeServiceDep = Annotated[SiteTypeService, Depends(get_site_type_service)]


def get_cost_category_service(uow: UnitOfWorkDep) -> CostCategoryService:
    return CostCategoryService(uow)


CostCategoryServiceDep = Annotated[
    CostCategoryService, Depends(get_cost_category_service)
]


def get_project_stage_service(uow: UnitOfWorkDep) -> ProjectStageService:
    return ProjectStageService(uow)


ProjectStageServiceDep = Annotated[
    ProjectStageService, Depends(get_project_stage_service)
]
