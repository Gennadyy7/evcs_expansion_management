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
    PROJECT_STAGE_ALLOWED_SORT_COLUMNS,
    PROJECT_STAGE_DEFAULT_SORT_BY,
    PROJECT_STAGE_DEFAULT_SORT_ORDER,
    ReferenceErrorCode,
)
from app.features.reference.messages import get_reference_message
from app.features.reference.models import ProjectStage
from app.features.reference.schemas.project_stage import (
    ProjectStageCreate,
    ProjectStageResponse,
    ProjectStageUpdate,
)

logger = get_logger(__name__)


class ProjectStageService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_project_stage(self, stage_no: int) -> ProjectStageResponse:
        project_stage = await self._get_project_stage_entity(stage_no)
        return ProjectStageResponse.model_validate(project_stage)

    async def list_project_stages(
        self,
        *,
        page: int,
        limit: int | None,
        sort_by: str | None,
        sort_order: str | None,
        search: str | None = None,
    ) -> PaginatedResponse[ProjectStageResponse]:
        pagination = build_pagination_params(page=page, requested_limit=limit)
        sort = resolve_sort_params(
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_columns=PROJECT_STAGE_ALLOWED_SORT_COLUMNS,
            default_sort_by=PROJECT_STAGE_DEFAULT_SORT_BY,
            default_sort_order=PROJECT_STAGE_DEFAULT_SORT_ORDER,
        )
        items, total_items = await self._uow.project_stages.list_paginated(
            limit=pagination.limit,
            offset=pagination.offset,
            sort=sort,
            search=search,
        )
        response_items = [ProjectStageResponse.model_validate(item) for item in items]
        return build_paginated_response(
            response_items,
            total_items=total_items,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def create_project_stage(
        self, payload: ProjectStageCreate
    ) -> ProjectStageResponse:
        existing = await self._uow.project_stages.get_by_id(payload.stage_no)
        if existing is not None:
            self._raise_already_exists(payload.stage_no)

        existing = await self._uow.project_stages.get_by_code(payload.code)
        if existing is not None:
            self._raise_code_already_exists(payload.code)

        project_stage = ProjectStage(
            stage_no=payload.stage_no,
            code=payload.code,
            name_ru=payload.name_ru,
            is_milestone=payload.is_milestone,
        )
        created = await self._uow.project_stages.create(project_stage)
        await self._uow.commit()
        logger.info(
            f'Created project_stage stage_no={created.stage_no}, code={created.code!r}'
        )
        return ProjectStageResponse.model_validate(created)

    async def update_project_stage(
        self,
        stage_no: int,
        payload: ProjectStageUpdate,
    ) -> ProjectStageResponse:
        project_stage = await self._get_project_stage_entity(stage_no)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return ProjectStageResponse.model_validate(project_stage)

        if 'code' in update_data and update_data['code'] is not None:
            new_code = str(update_data['code'])
            if new_code != project_stage.code:
                existing = await self._uow.project_stages.get_by_code(new_code)
                if existing is not None and existing.stage_no != stage_no:
                    self._raise_code_already_exists(new_code)
            project_stage.code = new_code

        if 'name_ru' in update_data and update_data['name_ru'] is not None:
            project_stage.name_ru = str(update_data['name_ru'])

        if 'is_milestone' in update_data:
            project_stage.is_milestone = update_data['is_milestone']

        updated = await self._uow.project_stages.update(project_stage)
        await self._uow.commit()
        logger.info(
            f'Updated project_stage stage_no={updated.stage_no}, code={updated.code!r}'
        )
        return ProjectStageResponse.model_validate(updated)

    async def delete_project_stage(self, stage_no: int) -> None:
        project_stage = await self._get_project_stage_entity(stage_no)

        if await self._uow.project_stages.has_linked_entities(stage_no):
            self._raise_in_use(stage_no)

        await self._uow.project_stages.delete(project_stage)
        await self._uow.commit()
        logger.info(
            f'Deleted project_stage stage_no={stage_no}, code={project_stage.code!r}'
        )

    async def _get_project_stage_entity(self, stage_no: int) -> ProjectStage:
        project_stage = await self._uow.project_stages.get_by_id(stage_no)
        if project_stage is None:
            self._raise_not_found(stage_no)
        return project_stage

    def _raise_not_found(self, stage_no: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': ReferenceErrorCode.PROJECT_STAGE_NOT_FOUND,
                'message': get_reference_message(
                    ReferenceErrorCode.PROJECT_STAGE_NOT_FOUND
                ),
                'stage_no': stage_no,
            },
        )

    def _raise_already_exists(self, stage_no: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.PROJECT_STAGE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.PROJECT_STAGE_ALREADY_EXISTS
                ),
                'stage_no': stage_no,
            },
        )

    def _raise_code_already_exists(self, code: str) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.PROJECT_STAGE_CODE_ALREADY_EXISTS,
                'message': get_reference_message(
                    ReferenceErrorCode.PROJECT_STAGE_CODE_ALREADY_EXISTS
                ),
                'code_value': code,
            },
        )

    def _raise_in_use(self, stage_no: int) -> NoReturn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': ReferenceErrorCode.PROJECT_STAGE_IN_USE,
                'message': get_reference_message(
                    ReferenceErrorCode.PROJECT_STAGE_IN_USE
                ),
                'stage_no': stage_no,
            },
        )
