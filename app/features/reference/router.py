from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from app.core.pagination import PaginatedResponse
from app.features.reference.constants import (
    REGION_TREE_DEFAULT_DEPTH,
    REGION_TREE_MAX_DEPTH,
)
from app.features.reference.dependencies import RegionServiceDep
from app.features.reference.schemas.region import (
    RegionCreate,
    RegionResponse,
    RegionTree,
    RegionUpdate,
)

router = APIRouter(prefix='/reference')

_REGIONS_TAG = 'Reference: Regions'


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
