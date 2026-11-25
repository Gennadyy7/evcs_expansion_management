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
    CHARGER_TYPE_ALLOWED_SORT_COLUMNS,
    CHARGER_TYPE_DEFAULT_SORT_BY,
    CHARGER_TYPE_DEFAULT_SORT_ORDER,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import ChargerType
from app.features.reference.schemas.charger_type import (
    ChargerTypeCreate,
    ChargerTypeResponse,
    ChargerTypeUpdate,
)

logger = get_logger(__name__)


class ChargerTypeService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_charger_type(self, charger_type_id: int) -> ChargerTypeResponse:
        charger_type = await self._get_charger_type_entity(charger_type_id)
        return ChargerTypeResponse.model_validate(charger_type)

    async def list_charger_types(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
    ) -> PaginatedResponse[ChargerTypeResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=CHARGER_TYPE_ALLOWED_SORT_COLUMNS,
            default_sort_by=CHARGER_TYPE_DEFAULT_SORT_BY,
            default_sort_order=CHARGER_TYPE_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.charger_types.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
        )
        response_items = [ChargerTypeResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_charger_type(
        self, payload: ChargerTypeCreate
    ) -> ChargerTypeResponse:
        existing = await self._uow.charger_types.get_by_code(payload.code)
        if existing is not None:
            self._raise_code_already_exists(payload.code)

        charger_type = ChargerType(
            code=payload.code,
            name_ru=payload.name_ru,
            description=payload.description,
        )
        created = await self._uow.charger_types.create(charger_type)
        await self._uow.commit()
        logger.info(
            f'Created charger_type charger_type_id={created.charger_type_id}, '
            f'code={created.code!r}'
        )
        return ChargerTypeResponse.model_validate(created)

    async def update_charger_type(
        self,
        charger_type_id: int,
        payload: ChargerTypeUpdate,
    ) -> ChargerTypeResponse:
        charger_type = await self._get_charger_type_entity(charger_type_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return ChargerTypeResponse.model_validate(charger_type)

        if 'code' in update_data and update_data['code'] is not None:
            new_code = str(update_data['code'])
            if new_code != charger_type.code:
                existing = await self._uow.charger_types.get_by_code(new_code)
                if existing is not None and existing.charger_type_id != charger_type_id:
                    self._raise_code_already_exists(new_code)
            charger_type.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            charger_type.name_ru = str(update_data['name_ru'])

        if 'description' in update_data:
            charger_type.description = update_data['description']

        updated = await self._uow.charger_types.update(charger_type)
        await self._uow.commit()
        logger.info(
            f'Updated charger_type charger_type_id={updated.charger_type_id}, '
            f'code={updated.code!r}'
        )
        return ChargerTypeResponse.model_validate(updated)

    async def delete_charger_type(self, charger_type_id: int) -> None:
        charger_type = await self._get_charger_type_entity(charger_type_id)

        if await self._uow.charger_types.has_linked_entities(charger_type_id):
            self._raise_in_use(charger_type_id)

        await self._uow.charger_types.delete(charger_type)
        await self._uow.commit()
        logger.info(
            f'Deleted charger_type charger_type_id={charger_type_id}, '
            f'code={charger_type.code!r}'
        )

    async def _get_charger_type_entity(self, charger_type_id: int) -> ChargerType:
        charger_type = await self._uow.charger_types.get_by_id(charger_type_id)
        if charger_type is None:
            self._raise_not_found(charger_type_id)
        return charger_type

    def _raise_not_found(self, charger_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.CHARGER_TYPE_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.CHARGER_TYPE_NOT_FOUND
                ),
                'charger_type_id': charger_type_id,
            },
        )

    def _raise_code_already_exists(self, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.CHARGER_TYPE_CODE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.CHARGER_TYPE_CODE_ALREADY_EXISTS
                ),
                'code_value': code,
            },
        )

    def _raise_in_use(self, charger_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.CHARGER_TYPE_IN_USE,
                'message': get_reference_message(
                    ReferenceErrorCode.CHARGER_TYPE_IN_USE
                ),
                'charger_type_id': charger_type_id,
            },
        )
