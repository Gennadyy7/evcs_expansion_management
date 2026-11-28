from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response, status

from app.core.pagination import PaginatedResponse
from app.features.core.constants import OrganizationKind
from app.features.core.dependencies import OrganizationServiceDep
from app.features.core.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter(prefix='/core')

_ORGANIZATIONS_TAG = 'Core: Organizations'


@router.get(
    '/organizations',
    response_model=PaginatedResponse[OrganizationResponse],
    tags=[_ORGANIZATIONS_TAG],
    summary='List organizations with pagination, sorting, search and filtering',
)
async def list_organizations(
    service: OrganizationServiceDep,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    limit: Annotated[
        int | None,
        Query(ge=1, description='Number of items per page'),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description=(
                'Sort field (organization_id, legal_name, '
                'registration_code, organization_kind, '
                'created_at, updated_at)'
            )
        ),
    ] = None,
    sort_order: Annotated[
        str | None,
        Query(description='Sort direction (asc, desc)'),
    ] = None,
    # max_length=200: long-text field (legal_name up to 500 chars in DB).
    # Short codes use max_length=100 per the reference-domain baseline.
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
            description='Search by legal name or registration code',
        ),
    ] = None,
    organization_kind: Annotated[
        OrganizationKind | None,
        Query(
            description=(
                'Filter by organization kind '
                '(owner, contractor, vendor, utility, other)'
            )
        ),
    ] = None,
) -> PaginatedResponse[OrganizationResponse]:
    return await service.list_organizations(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        organization_kind=organization_kind,
    )


@router.get(
    '/organizations/{organization_id}',
    response_model=OrganizationResponse,
    tags=[_ORGANIZATIONS_TAG],
    summary='Get organization by ID',
)
async def get_organization(
    service: OrganizationServiceDep,
    organization_id: Annotated[
        UUID, Path(description='Unique organization identifier')
    ],
) -> OrganizationResponse:
    return await service.get_organization(organization_id)


@router.post(
    '/organizations',
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[_ORGANIZATIONS_TAG],
    summary='Create a new organization',
)
async def create_organization(
    service: OrganizationServiceDep,
    payload: OrganizationCreate,
) -> OrganizationResponse:
    return await service.create_organization(payload)


@router.patch(
    '/organizations/{organization_id}',
    response_model=OrganizationResponse,
    tags=[_ORGANIZATIONS_TAG],
    summary='Partially update an organization',
)
async def update_organization(
    service: OrganizationServiceDep,
    organization_id: Annotated[
        UUID, Path(description='Unique organization identifier')
    ],
    payload: OrganizationUpdate,
) -> OrganizationResponse:
    return await service.update_organization(organization_id, payload)


@router.delete(
    '/organizations/{organization_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[_ORGANIZATIONS_TAG],
    summary='Delete an organization',
)
async def delete_organization(
    service: OrganizationServiceDep,
    organization_id: Annotated[
        UUID, Path(description='Unique organization identifier')
    ],
) -> Response:
    await service.delete_organization(organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
