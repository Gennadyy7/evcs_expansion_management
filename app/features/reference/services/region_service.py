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
    REGION_ALLOWED_SORT_COLUMNS,
    REGION_DEFAULT_SORT_BY,
    REGION_DEFAULT_SORT_ORDER,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import Region
from app.features.reference.schemas.region import (
    RegionCreate,
    RegionResponse,
    RegionTree,
    RegionUpdate,
)

logger = get_logger(__name__)


class RegionService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_region(self, region_id: int) -> RegionResponse:
        region = await self._get_region_entity(region_id)
        return RegionResponse.model_validate(region)

    async def list_regions(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        parent_region_id: int | None = None,
        root_only: bool = False,
        search: str | None = None,
    ) -> PaginatedResponse[RegionResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=REGION_ALLOWED_SORT_COLUMNS,
            default_sort_by=REGION_DEFAULT_SORT_BY,
            default_sort_order=REGION_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.regions.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            parent_region_id=parent_region_id,
            root_only=root_only,
            search=search,
        )
        response_items = [RegionResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def get_regions_tree(self, *, depth: int) -> list[RegionTree]:
        regions = await self._uow.regions.get_root_regions_with_tree(depth=depth)
        return [RegionTree.model_validate(region) for region in regions]

    async def get_region_subtree(self, region_id: int, *, depth: int) -> RegionTree:
        region = await self._uow.regions.get_region_with_tree(
            region_id=region_id,
            depth=depth,
        )
        if region is None:
            self._raise_region_not_found(region_id)
        return RegionTree.model_validate(region)

    async def create_region(self, payload: RegionCreate) -> RegionResponse:
        existing = await self._uow.regions.get_by_code(payload.code)
        if existing is not None:
            self._raise_code_already_exists(payload.code)

        if payload.parent_region_id is not None:
            parent = await self._uow.regions.get_by_id(payload.parent_region_id)
            if parent is None:
                self._raise_parent_not_found(payload.parent_region_id)

        region = Region(
            code=payload.code,
            name_ru=payload.name_ru,
            parent_region_id=payload.parent_region_id,
        )
        created = await self._uow.regions.create(region)
        await self._uow.commit()
        logger.info(
            f'Created region region_id={created.region_id}, code={created.code!r}'
        )
        return RegionResponse.model_validate(created)

    async def update_region(
        self,
        region_id: int,
        payload: RegionUpdate,
    ) -> RegionResponse:
        region = await self._get_region_entity(region_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return RegionResponse.model_validate(region)

        if 'code' in update_data and update_data['code'] is not None:
            new_code = str(update_data['code'])
            if new_code != region.code:
                existing = await self._uow.regions.get_by_code(new_code)
                if existing is not None and existing.region_id != region_id:
                    self._raise_code_already_exists(new_code)
            region.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            region.name_ru = str(update_data['name_ru'])

        if 'parent_region_id' in update_data:
            raw_parent_id = update_data['parent_region_id']
            new_parent_id = int(raw_parent_id) if raw_parent_id is not None else None

            if new_parent_id is not None:
                new_parent_id: int  # type: ignore[no-redef]
                if new_parent_id == region_id:
                    self._raise_self_parent(region_id)

                parent = await self._uow.regions.get_by_id(new_parent_id)
                if parent is None:
                    self._raise_parent_not_found(new_parent_id)

                if await self._uow.regions.is_descendant(region_id, new_parent_id):
                    self._raise_cycle_detected(region_id, new_parent_id)

            region.parent_region_id = new_parent_id

        updated = await self._uow.regions.update(region)
        await self._uow.commit()
        logger.info(
            f'Updated region region_id={updated.region_id}, code={updated.code!r}'
        )
        return RegionResponse.model_validate(updated)

    async def delete_region(self, region_id: int) -> None:
        region = await self._get_region_entity(region_id)

        if await self._uow.regions.has_children(region_id):
            self._raise_has_children(region_id)

        if await self._uow.regions.has_linked_entities(region_id):
            self._raise_region_in_use(region_id)

        await self._uow.regions.delete(region)
        await self._uow.commit()
        logger.info(f'Deleted region region_id={region_id}, code={region.code!r}')

    async def _get_region_entity(self, region_id: int) -> Region:
        region = await self._uow.regions.get_by_id(region_id)
        if region is None:
            self._raise_region_not_found(region_id)
        return region

    def _raise_region_not_found(self, region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.REGION_NOT_FOUND,
                'message': get_reference_message(ReferenceErrorCode.REGION_NOT_FOUND),
                'region_id': region_id,
            },
        )

    def _raise_code_already_exists(self, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.REGION_CODE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.REGION_CODE_ALREADY_EXISTS
                ),
                'code_value': code,
            },
        )

    def _raise_parent_not_found(self, parent_region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.REGION_PARENT_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.REGION_PARENT_NOT_FOUND
                ),
                'parent_region_id': parent_region_id,
            },
        )

    def _raise_self_parent(self, region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                'code': ReferenceErrorCode.REGION_SELF_PARENT,
                'message': get_reference_message(ReferenceErrorCode.REGION_SELF_PARENT),
                'region_id': region_id,
            },
        )

    def _raise_cycle_detected(self, region_id: int, parent_region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                'code': ReferenceErrorCode.REGION_CYCLE_DETECTED,
                'message': get_reference_message(
                    ReferenceErrorCode.REGION_CYCLE_DETECTED
                ),
                'region_id': region_id,
                'parent_region_id': parent_region_id,
            },
        )

    def _raise_has_children(self, region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.REGION_HAS_CHILDREN,
                'message': get_reference_message(
                    ReferenceErrorCode.REGION_HAS_CHILDREN
                ),
                'region_id': region_id,
            },
        )

    def _raise_region_in_use(self, region_id: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.REGION_IN_USE,
                'message': get_reference_message(ReferenceErrorCode.REGION_IN_USE),
                'region_id': region_id,
            },
        )
