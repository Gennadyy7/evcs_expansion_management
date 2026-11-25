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
    CONNECTOR_TYPE_ALLOWED_SORT_COLUMNS,
    CONNECTOR_TYPE_DEFAULT_SORT_BY,
    CONNECTOR_TYPE_DEFAULT_SORT_ORDER,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import ConnectorType
from app.features.reference.schemas.connector_type import (
    ConnectorTypeCreate,
    ConnectorTypeResponse,
    ConnectorTypeUpdate,
)

logger = get_logger(__name__)


class ConnectorTypeService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_connector_type(self, connector_type_id: int) -> ConnectorTypeResponse:
        connector_type = await self._get_connector_type_entity(connector_type_id)
        return ConnectorTypeResponse.model_validate(connector_type)

    async def list_connector_types(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
    ) -> PaginatedResponse[ConnectorTypeResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=CONNECTOR_TYPE_ALLOWED_SORT_COLUMNS,
            default_sort_by=CONNECTOR_TYPE_DEFAULT_SORT_BY,
            default_sort_order=CONNECTOR_TYPE_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.connector_types.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
        )
        response_items = [ConnectorTypeResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_connector_type(
        self, payload: ConnectorTypeCreate
    ) -> ConnectorTypeResponse:
        existing = await self._uow.connector_types.get_by_code(payload.code)
        if existing is not None:
            self._raise_code_already_exists(payload.code)

        connector_type = ConnectorType(
            code=payload.code,
            name_ru=payload.name_ru,
        )
        created = await self._uow.connector_types.create(connector_type)
        await self._uow.commit()
        logger.info(
            f'Created connector_type connector_type_id={created.connector_type_id}, '
            f'code={created.code!r}'
        )
        return ConnectorTypeResponse.model_validate(created)

    async def update_connector_type(
        self,
        connector_type_id: int,
        payload: ConnectorTypeUpdate,
    ) -> ConnectorTypeResponse:
        connector_type = await self._get_connector_type_entity(connector_type_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return ConnectorTypeResponse.model_validate(connector_type)

        if 'code' in update_data and update_data['code'] is not None:
            new_code = str(update_data['code'])
            if new_code != connector_type.code:
                existing = await self._uow.connector_types.get_by_code(new_code)
                if (
                    existing is not None
                    and existing.connector_type_id != connector_type_id
                ):
                    self._raise_code_already_exists(new_code)
            connector_type.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            connector_type.name_ru = str(update_data['name_ru'])

        updated = await self._uow.connector_types.update(connector_type)
        await self._uow.commit()
        logger.info(
            f'Updated connector_type connector_type_id={updated.connector_type_id}, '
            f'code={updated.code!r}'
        )
        return ConnectorTypeResponse.model_validate(updated)

    async def delete_connector_type(self, connector_type_id: int) -> None:
        connector_type = await self._get_connector_type_entity(connector_type_id)

        if await self._uow.connector_types.has_linked_entities(connector_type_id):
            self._raise_in_use(connector_type_id)

        await self._uow.connector_types.delete(connector_type)
        await self._uow.commit()
        logger.info(
            f'Deleted connector_type connector_type_id={connector_type_id}, '
            f'code={connector_type.code!r}'
        )

    async def _get_connector_type_entity(self, connector_type_id: int) -> ConnectorType:
        connector_type = await self._uow.connector_types.get_by_id(connector_type_id)
        if connector_type is None:
            self._raise_not_found(connector_type_id)
        return connector_type

    def _raise_not_found(self, connector_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.CONNECTOR_TYPE_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.CONNECTOR_TYPE_NOT_FOUND
                ),
                'connector_type_id': connector_type_id,
            },
        )

    def _raise_code_already_exists(self, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.CONNECTOR_TYPE_CODE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.CONNECTOR_TYPE_CODE_ALREADY_EXISTS
                ),
                'code_value': code,
            },
        )

    def _raise_in_use(self, connector_type_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.CONNECTOR_TYPE_IN_USE,
                'message': get_reference_message(
                    ReferenceErrorCode.CONNECTOR_TYPE_IN_USE
                ),
                'connector_type_id': connector_type_id,
            },
        )
