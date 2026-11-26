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
    COST_CATEGORY_ALLOWED_SORT_COLUMNS,
    COST_CATEGORY_DEFAULT_SORT_BY,
    COST_CATEGORY_DEFAULT_SORT_ORDER,
    CostKind,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import CostCategory
from app.features.reference.schemas.cost_category import (
    CostCategoryCreate,
    CostCategoryResponse,
    CostCategoryUpdate,
)

logger = get_logger(__name__)


class CostCategoryService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_cost_category(self, category_id: int) -> CostCategoryResponse:
        category = await self._get_cost_category_entity(category_id)
        return CostCategoryResponse.model_validate(category)

    async def list_cost_categories(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
        cost_kind: CostKind | None = None,
    ) -> PaginatedResponse[CostCategoryResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=COST_CATEGORY_ALLOWED_SORT_COLUMNS,
            default_sort_by=COST_CATEGORY_DEFAULT_SORT_BY,
            default_sort_order=COST_CATEGORY_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.cost_categories.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
            cost_kind=cost_kind,
        )
        response_items = [CostCategoryResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_cost_category(
        self, payload: CostCategoryCreate
    ) -> CostCategoryResponse:
        existing = await self._uow.cost_categories.get_by_kind_and_code(
            payload.cost_kind, payload.code
        )
        if existing is not None:
            self._raise_already_exists(str(payload.cost_kind), payload.code)

        cost_category = CostCategory(
            cost_kind=payload.cost_kind,
            code=payload.code,
            name_ru=payload.name_ru,
        )
        created = await self._uow.cost_categories.create(cost_category)
        await self._uow.commit()
        logger.info(
            f'Created cost_category category_id={created.category_id}, '
            f'cost_kind={created.cost_kind!r}, code={created.code!r}'
        )
        return CostCategoryResponse.model_validate(created)

    async def update_cost_category(
        self,
        category_id: int,
        payload: CostCategoryUpdate,
    ) -> CostCategoryResponse:
        category = await self._get_cost_category_entity(category_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return CostCategoryResponse.model_validate(category)

        new_cost_kind_str = (
            str(update_data['cost_kind'])
            if 'cost_kind' in update_data and update_data['cost_kind'] is not None
            else category.cost_kind
        )
        new_code = (
            str(update_data['code'])
            if 'code' in update_data and update_data['code'] is not None
            else category.code
        )

        if new_cost_kind_str != category.cost_kind or new_code != category.code:
            existing = await self._uow.cost_categories.get_by_kind_and_code(
                CostKind(new_cost_kind_str), new_code
            )
            if existing is not None and existing.category_id != category_id:
                self._raise_already_exists(new_cost_kind_str, new_code)

        if (
            new_cost_kind_str != category.cost_kind
            and await self._uow.cost_categories.has_linked_entities(
                category.category_id, category.cost_kind
            )
        ):
            self._raise_in_use(category_id)

        category.cost_kind = new_cost_kind_str
        category.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            category.name_ru = str(update_data['name_ru'])

        updated = await self._uow.cost_categories.update(category)
        await self._uow.commit()
        logger.info(
            f'Updated cost_category category_id={updated.category_id}, '
            f'cost_kind={updated.cost_kind!r}, code={updated.code!r}'
        )
        return CostCategoryResponse.model_validate(updated)

    async def delete_cost_category(self, category_id: int) -> None:
        category = await self._get_cost_category_entity(category_id)

        if await self._uow.cost_categories.has_linked_entities(
            category.category_id, category.cost_kind
        ):
            self._raise_in_use(category_id)

        await self._uow.cost_categories.delete(category)
        await self._uow.commit()
        logger.info(
            f'Deleted cost_category category_id={category_id}, '
            f'cost_kind={category.cost_kind!r}, code={category.code!r}'
        )

    async def _get_cost_category_entity(self, category_id: int) -> CostCategory:
        category = await self._uow.cost_categories.get_by_id(category_id)
        if category is None:
            self._raise_not_found(category_id)
        return category

    def _raise_not_found(self, category_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.COST_CATEGORY_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.COST_CATEGORY_NOT_FOUND
                ),
                'category_id': category_id,
            },
        )

    def _raise_already_exists(self, cost_kind: str, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.COST_CATEGORY_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.COST_CATEGORY_ALREADY_EXISTS
                ),
                'cost_kind': cost_kind,
                'code_value': code,
            },
        )

    def _raise_in_use(self, category_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.COST_CATEGORY_IN_USE,
                'message': get_reference_message(
                    ReferenceErrorCode.COST_CATEGORY_IN_USE
                ),
                'category_id': category_id,
            },
        )
