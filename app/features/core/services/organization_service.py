from typing import NoReturn
from uuid import UUID

from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.core.pagination import (
    PaginatedResponse,
    build_paginated_response,
    build_pagination_params,
)
from app.core.query_params import resolve_sort_params
from app.core.unit_of_work.protocol import UnitOfWorkProtocol
from app.features.core.constants import (
    ORGANIZATION_ALLOWED_SORT_COLUMNS,
    ORGANIZATION_DEFAULT_SORT_BY,
    ORGANIZATION_DEFAULT_SORT_ORDER,
    CoreErrorCode,
    OrganizationKind,
)
from app.features.core.messages import get_core_message
from app.features.core.models import Organization
from app.features.core.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

logger = get_logger(__name__)


class OrganizationService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_organization(self, organization_id: UUID) -> OrganizationResponse:
        organization = await self._get_organization_entity(organization_id)
        return OrganizationResponse.model_validate(organization)

    async def list_organizations(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
        organization_kind: OrganizationKind | None = None,
    ) -> PaginatedResponse[OrganizationResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=ORGANIZATION_ALLOWED_SORT_COLUMNS,
            default_sort_by=ORGANIZATION_DEFAULT_SORT_BY,
            default_sort_order=ORGANIZATION_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.organizations.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
            organization_kind=organization_kind,
        )
        response_items = [OrganizationResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_organization(
        self, payload: OrganizationCreate
    ) -> OrganizationResponse:
        registration_code = payload.registration_code
        if registration_code is not None:
            registration_code = registration_code.strip() or None

        if registration_code is not None:
            existing = await self._uow.organizations.get_by_registration_code(
                registration_code
            )
            if existing is not None:
                self._raise_registration_code_exists(registration_code)

        organization = Organization(
            legal_name=payload.legal_name,
            registration_code=registration_code,
            organization_kind=payload.organization_kind,
        )
        created = await self._uow.organizations.create(organization)
        await self._uow.commit()
        logger.info(
            f'Created organization '
            f'organization_id={created.organization_id}, '
            f'legal_name={created.legal_name!r}'
        )
        return OrganizationResponse.model_validate(created)

    async def update_organization(
        self,
        organization_id: UUID,
        payload: OrganizationUpdate,
    ) -> OrganizationResponse:
        organization = await self._get_organization_entity(organization_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return OrganizationResponse.model_validate(organization)

        if 'registration_code' in update_data:
            new_code = update_data['registration_code']
            if new_code is not None:
                new_code = new_code.strip() or None

            if new_code != organization.registration_code:
                if new_code is not None:
                    existing = await self._uow.organizations.get_by_registration_code(
                        new_code
                    )
                    if (
                        existing is not None
                        and existing.organization_id != organization_id
                    ):
                        self._raise_registration_code_exists(new_code)
                organization.registration_code = new_code

        if 'legal_name' in update_data and update_data['legal_name'] is not None:
            organization.legal_name = update_data['legal_name']

        if (
            'organization_kind' in update_data
            and update_data['organization_kind'] is not None
        ):
            organization.organization_kind = update_data['organization_kind']

        updated = await self._uow.organizations.update(organization)
        await self._uow.commit()
        logger.info(
            f'Updated organization '
            f'organization_id={updated.organization_id}, '
            f'legal_name={updated.legal_name!r}'
        )
        return OrganizationResponse.model_validate(updated)

    async def delete_organization(self, organization_id: UUID) -> None:
        organization = await self._get_organization_entity(organization_id)

        if await self._uow.organizations.has_linked_entities(organization_id):
            self._raise_in_use(organization_id)

        await self._uow.organizations.delete(organization)
        await self._uow.commit()
        logger.info(
            f'Deleted organization '
            f'organization_id={organization_id}, '
            f'legal_name={organization.legal_name!r}'
        )

    async def _get_organization_entity(self, organization_id: UUID) -> Organization:
        organization = await self._uow.organizations.get_by_id(organization_id)
        if organization is None:
            self._raise_not_found(organization_id)
        return organization

    def _raise_not_found(self, organization_id: UUID) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': CoreErrorCode.ORGANIZATION_NOT_FOUND,
                'message': get_core_message(CoreErrorCode.ORGANIZATION_NOT_FOUND),
                'organization_id': str(organization_id),
            },
        )

    def _raise_registration_code_exists(self, registration_code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': CoreErrorCode.ORGANIZATION_REGISTRATION_CODE_EXISTS,
                'message': get_core_message(
                    CoreErrorCode.ORGANIZATION_REGISTRATION_CODE_EXISTS
                ),
                'registration_code': registration_code,
            },
        )

    def _raise_in_use(self, organization_id: UUID) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': CoreErrorCode.ORGANIZATION_IN_USE,
                'message': get_core_message(CoreErrorCode.ORGANIZATION_IN_USE),
                'organization_id': str(organization_id),
            },
        )
