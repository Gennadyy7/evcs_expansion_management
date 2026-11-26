from typing import NoReturn

from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.core.pagination import (
    PaginatedResponse,
    build_paginated_response,
    build_pagination_params,
)
from app.core.query_params import resolve_sort_params
from app.core.unit_of_work.protocol import UnitOfWorkProtocol
from app.features.reference.constants import (
    SITE_TYPE_ALLOWED_SORT_COLUMNS,
    SITE_TYPE_DEFAULT_SORT_BY,
    SITE_TYPE_DEFAULT_SORT_ORDER,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import SiteType
from app.features.reference.schemas.site_type import (
    SiteTypeCreate,
    SiteTypeResponse,
    SiteTypeUpdate,
)

logger = get_logger(__name__)


class SiteTypeService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_site_type(self, site_type_id: int) -> SiteTypeResponse:
        site_type = await self._get_site_type_entity(site_type_id)
        return SiteTypeResponse.model_validate(site_type)

    async def list_site_types(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
    ) -> PaginatedResponse[SiteTypeResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=SITE_TYPE_ALLOWED_SORT_COLUMNS,
            default_sort_by=SITE_TYPE_DEFAULT_SORT_BY,
            default_sort_order=SITE_TYPE_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.site_types.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
        )
        response_items = [SiteTypeResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_site_type(self, payload: SiteTypeCreate) -> SiteTypeResponse:
        existing = await self._uow.site_types.get_by_code(payload.code)
        if existing is not None:
            self._raise_code_already_exists(payload.code)

        site_type = SiteType(
            code=payload.code,
            name_ru=payload.name_ru,
        )
        created = await self._uow.site_types.create(site_type)
        await self._uow.commit()
        logger.info(
            f'Created site_type site_type_id={created.site_type_id}, '
            f'code={created.code!r}'
        )
        return SiteTypeResponse.model_validate(created)

    async def update_site_type(
        self,
        site_type_id: int,
        payload: SiteTypeUpdate,
    ) -> SiteTypeResponse:
        site_type = await self._get_site_type_entity(site_type_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return SiteTypeResponse.model_validate(site_type)

        if 'code' in update_data and update_data['code'] is not None:
            new_code = str(update_data['code'])
            if new_code != site_type.code:
                existing = await self._uow.site_types.get_by_code(new_code)
                if existing is not None and existing.site_type_id != site_type_id:
                    self._raise_code_already_exists(new_code)
            site_type.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            site_type.name_ru = str(update_data['name_ru'])

        updated = await self._uow.site_types.update(site_type)
        await self._uow.commit()
        logger.info(
            f'Updated site_type site_type_id={updated.site_type_id}, '
            f'code={updated.code!r}'
        )
        return SiteTypeResponse.model_validate(updated)

    async def delete_site_type(self, site_type_id: int) -> None:
        site_type = await self._get_site_type_entity(site_type_id)

        if await self._uow.site_types.has_linked_entities(site_type_id):
            self._raise_in_use(site_type_id)

        await self._uow.site_types.delete(site_type)
        await self._uow.commit()
        logger.info(
            f'Deleted site_type site_type_id={site_type_id}, code={site_type.code!r}'
        )

    async def _get_site_type_entity(self, site_type_id: int) -> SiteType:
        site_type = await self._uow.site_types.get_by_id(site_type_id)
        if site_type is None:
            self._raise_not_found(site_type_id)
        return site_type

    def _raise_not_found(self, site_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.SITE_TYPE_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.SITE_TYPE_NOT_FOUND
                ),
                'site_type_id': site_type_id,
            },
        )

    def _raise_code_already_exists(self, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.SITE_TYPE_CODE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.SITE_TYPE_CODE_ALREADY_EXISTS
                ),
                'code_value': code,
            },
        )

    def _raise_in_use(self, site_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.SITE_TYPE_IN_USE,
                'message': get_reference_message(ReferenceErrorCode.SITE_TYPE_IN_USE),
                'site_type_id': site_type_id,
            },
        )
