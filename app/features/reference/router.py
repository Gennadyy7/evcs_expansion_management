from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from app.core.pagination import PaginatedResponse
from app.features.reference.constants import (
    REGION_TREE_DEFAULT_DEPTH,
    REGION_TREE_MAX_DEPTH,
)
from app.features.reference.dependencies import (
    ChargerTypeServiceDep,
    ConnectorTypeServiceDep,
    RegionServiceDep,
    SiteTypeServiceDep,
)
from app.features.reference.schemas.charger_type import (
    ChargerTypeCreate,
    ChargerTypeResponse,
    ChargerTypeUpdate,
)
from app.features.reference.schemas.connector_type import (
    ConnectorTypeCreate,
    ConnectorTypeResponse,
    ConnectorTypeUpdate,
)
from app.features.reference.schemas.region import (
    RegionCreate,
    RegionResponse,
    RegionTree,
    RegionUpdate,
)
from app.features.reference.schemas.site_type import (
    SiteTypeCreate,
    SiteTypeResponse,
    SiteTypeUpdate,
)

router = APIRouter(prefix='/reference')

_REGIONS_TAG = 'Reference: Regions'
_CHARGER_TYPES_TAG = 'Reference: Charger Types'
_CONNECTOR_TYPES_TAG = 'Reference: Connector Types'
_SITE_TYPES_TAG = 'Reference: Site Types'


# Regions


@router.get(
    '/regions',
    response_model=PaginatedResponse[RegionResponse],
    tags=[_REGIONS_TAG],
    summary='List regions with pagination and filtering',
)
async def list_regions(
    service: RegionServiceDep,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    limit: Annotated[
        int | None,
        Query(ge=1, description='Number of items per page'),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description='Sort field (region_id, code, name_ru, created_at, updated_at)'
        ),
    ] = None,
    sort_order: Annotated[
        str | None,
        Query(description='Sort direction (asc, desc)'),
    ] = None,
    parent_region_id: Annotated[
        int | None,
        Query(gt=0, description='Filter by parent region ID'),
    ] = None,
    root_only: Annotated[
        bool,
        Query(description='Return only root regions (without parent)'),
    ] = False,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description='Search by region code or name',
        ),
    ] = None,
) -> PaginatedResponse[RegionResponse]:
    return await service.list_regions(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        parent_region_id=parent_region_id,
        root_only=root_only,
        search=search,
    )


@router.get(
    '/regions/tree',
    response_model=list[RegionTree],
    tags=[_REGIONS_TAG],
    summary='Get hierarchical tree of regions',
)
async def get_regions_tree(
    service: RegionServiceDep,
    depth: Annotated[
        int,
        Query(
            ge=0,
            le=REGION_TREE_MAX_DEPTH,
            description='Depth of nested child regions',
        ),
    ] = REGION_TREE_DEFAULT_DEPTH,
) -> list[RegionTree]:
    return await service.get_regions_tree(depth=depth)


@router.get(
    '/regions/{region_id}',
    response_model=RegionResponse,
    tags=[_REGIONS_TAG],
    summary='Get region by ID',
)
async def get_region(
    service: RegionServiceDep,
    region_id: Annotated[int, Path(gt=0, description='Unique region identifier')],
) -> RegionResponse:
    return await service.get_region(region_id)


@router.get(
    '/regions/{region_id}/tree',
    response_model=RegionTree,
    tags=[_REGIONS_TAG],
    summary='Get subtree of child regions for a given region',
)
async def get_region_subtree(
    service: RegionServiceDep,
    region_id: Annotated[int, Path(gt=0, description='Unique region identifier')],
    depth: Annotated[
        int,
        Query(
            ge=0,
            le=REGION_TREE_MAX_DEPTH,
            description='Depth of nested child regions',
        ),
    ] = REGION_TREE_DEFAULT_DEPTH,
) -> RegionTree:
    return await service.get_region_subtree(region_id, depth=depth)


@router.post(
    '/regions',
    response_model=RegionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[_REGIONS_TAG],
    summary='Create a new region',
)
async def create_region(
    service: RegionServiceDep,
    payload: RegionCreate,
) -> RegionResponse:
    return await service.create_region(payload)


@router.patch(
    '/regions/{region_id}',
    response_model=RegionResponse,
    tags=[_REGIONS_TAG],
    summary='Partially update a region',
)
async def update_region(
    service: RegionServiceDep,
    region_id: Annotated[int, Path(gt=0, description='Unique region identifier')],
    payload: RegionUpdate,
) -> RegionResponse:
    return await service.update_region(region_id, payload)


@router.delete(
    '/regions/{region_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[_REGIONS_TAG],
    summary='Delete a region',
)
async def delete_region(
    service: RegionServiceDep,
    region_id: Annotated[int, Path(gt=0, description='Unique region identifier')],
) -> Response:
    await service.delete_region(region_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Charger Types


@router.get(
    '/charger-types',
    response_model=PaginatedResponse[ChargerTypeResponse],
    tags=[_CHARGER_TYPES_TAG],
    summary='List charger types with pagination, sorting and search',
)
async def list_charger_types(
    service: ChargerTypeServiceDep,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    limit: Annotated[
        int | None,
        Query(ge=1, description='Number of items per page'),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description=(
                'Sort field (charger_type_id, code, name_ru, created_at, updated_at)'
            )
        ),
    ] = None,
    sort_order: Annotated[
        str | None,
        Query(description='Sort direction (asc, desc)'),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description='Search by code, name or description',
        ),
    ] = None,
) -> PaginatedResponse[ChargerTypeResponse]:
    return await service.list_charger_types(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


@router.get(
    '/charger-types/{charger_type_id}',
    response_model=ChargerTypeResponse,
    tags=[_CHARGER_TYPES_TAG],
    summary='Get charger type by ID',
)
async def get_charger_type(
    service: ChargerTypeServiceDep,
    charger_type_id: Annotated[
        int, Path(gt=0, description='Unique charger type identifier')
    ],
) -> ChargerTypeResponse:
    return await service.get_charger_type(charger_type_id)


@router.post(
    '/charger-types',
    response_model=ChargerTypeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[_CHARGER_TYPES_TAG],
    summary='Create a new charger type',
)
async def create_charger_type(
    service: ChargerTypeServiceDep,
    payload: ChargerTypeCreate,
) -> ChargerTypeResponse:
    return await service.create_charger_type(payload)


@router.patch(
    '/charger-types/{charger_type_id}',
    response_model=ChargerTypeResponse,
    tags=[_CHARGER_TYPES_TAG],
    summary='Partially update a charger type',
)
async def update_charger_type(
    service: ChargerTypeServiceDep,
    charger_type_id: Annotated[
        int, Path(gt=0, description='Unique charger type identifier')
    ],
    payload: ChargerTypeUpdate,
) -> ChargerTypeResponse:
    return await service.update_charger_type(charger_type_id, payload)


@router.delete(
    '/charger-types/{charger_type_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[_CHARGER_TYPES_TAG],
    summary='Delete a charger type',
)
async def delete_charger_type(
    service: ChargerTypeServiceDep,
    charger_type_id: Annotated[
        int, Path(gt=0, description='Unique charger type identifier')
    ],
) -> Response:
    await service.delete_charger_type(charger_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Connector Types


@router.get(
    '/connector-types',
    response_model=PaginatedResponse[ConnectorTypeResponse],
    tags=[_CONNECTOR_TYPES_TAG],
    summary='List connector types with pagination, sorting and search',
)
async def list_connector_types(
    service: ConnectorTypeServiceDep,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    limit: Annotated[
        int | None,
        Query(ge=1, description='Number of items per page'),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description=(
                'Sort field (connector_type_id, code, name_ru, created_at, updated_at)'
            )
        ),
    ] = None,
    sort_order: Annotated[
        str | None,
        Query(description='Sort direction (asc, desc)'),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description='Search by code or name',
        ),
    ] = None,
) -> PaginatedResponse[ConnectorTypeResponse]:
    return await service.list_connector_types(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


@router.get(
    '/connector-types/{connector_type_id}',
    response_model=ConnectorTypeResponse,
    tags=[_CONNECTOR_TYPES_TAG],
    summary='Get connector type by ID',
)
async def get_connector_type(
    service: ConnectorTypeServiceDep,
    connector_type_id: Annotated[
        int, Path(gt=0, description='Unique connector type identifier')
    ],
) -> ConnectorTypeResponse:
    return await service.get_connector_type(connector_type_id)


@router.post(
    '/connector-types',
    response_model=ConnectorTypeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[_CONNECTOR_TYPES_TAG],
    summary='Create a new connector type',
)
async def create_connector_type(
    service: ConnectorTypeServiceDep,
    payload: ConnectorTypeCreate,
) -> ConnectorTypeResponse:
    return await service.create_connector_type(payload)


@router.patch(
    '/connector-types/{connector_type_id}',
    response_model=ConnectorTypeResponse,
    tags=[_CONNECTOR_TYPES_TAG],
    summary='Partially update a connector type',
)
async def update_connector_type(
    service: ConnectorTypeServiceDep,
    connector_type_id: Annotated[
        int, Path(gt=0, description='Unique connector type identifier')
    ],
    payload: ConnectorTypeUpdate,
) -> ConnectorTypeResponse:
    return await service.update_connector_type(connector_type_id, payload)


@router.delete(
    '/connector-types/{connector_type_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[_CONNECTOR_TYPES_TAG],
    summary='Delete a connector type',
)
async def delete_connector_type(
    service: ConnectorTypeServiceDep,
    connector_type_id: Annotated[
        int, Path(gt=0, description='Unique connector type identifier')
    ],
) -> Response:
    await service.delete_connector_type(connector_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Site Types


@router.get(
    '/site-types',
    response_model=PaginatedResponse[SiteTypeResponse],
    tags=[_SITE_TYPES_TAG],
    summary='List site types with pagination, sorting and search',
)
async def list_site_types(
    service: SiteTypeServiceDep,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    limit: Annotated[
        int | None,
        Query(ge=1, description='Number of items per page'),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description=(
                'Sort field (site_type_id, code, name_ru, created_at, updated_at)'
            )
        ),
    ] = None,
    sort_order: Annotated[
        str | None,
        Query(description='Sort direction (asc, desc)'),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description='Search by code or name',
        ),
    ] = None,
) -> PaginatedResponse[SiteTypeResponse]:
    return await service.list_site_types(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )


@router.get(
    '/site-types/{site_type_id}',
    response_model=SiteTypeResponse,
    tags=[_SITE_TYPES_TAG],
    summary='Get site type by ID',
)
async def get_site_type(
    service: SiteTypeServiceDep,
    site_type_id: Annotated[int, Path(gt=0, description='Unique site type identifier')],
) -> SiteTypeResponse:
    return await service.get_site_type(site_type_id)


@router.post(
    '/site-types',
    response_model=SiteTypeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[_SITE_TYPES_TAG],
    summary='Create a new site type',
)
async def create_site_type(
    service: SiteTypeServiceDep,
    payload: SiteTypeCreate,
) -> SiteTypeResponse:
    return await service.create_site_type(payload)


@router.patch(
    '/site-types/{site_type_id}',
    response_model=SiteTypeResponse,
    tags=[_SITE_TYPES_TAG],
    summary='Partially update a site type',
)
async def update_site_type(
    service: SiteTypeServiceDep,
    site_type_id: Annotated[int, Path(gt=0, description='Unique site type identifier')],
    payload: SiteTypeUpdate,
) -> SiteTypeResponse:
    return await service.update_site_type(site_type_id, payload)


@router.delete(
    '/site-types/{site_type_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[_SITE_TYPES_TAG],
    summary='Delete a site type',
)
async def delete_site_type(
    service: SiteTypeServiceDep,
    site_type_id: Annotated[int, Path(gt=0, description='Unique site type identifier')],
) -> Response:
    await service.delete_site_type(site_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
