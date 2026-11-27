from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, UnaryExpression, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.logging import get_logger
from app.core.query_params import SortParams
from app.core.repositories.sqlalchemy import SQLAlchemyRepository
from app.features.core.constants import OrganizationKind
from app.features.core.models import GridConnection, Organization, Site
from app.features.pm.models import Contract, Issue, Permit, StageExecution
from app.features.reference.repositories.utils import escape_like_pattern

logger = get_logger(__name__)

_ORGANIZATION_SORT_COLUMNS: dict[str, InstrumentedAttribute[object]] = {
    'organization_id': Organization.organization_id,
    'legal_name': Organization.legal_name,
    'registration_code': Organization.registration_code,
    'organization_kind': Organization.organization_kind,
    'created_at': Organization.created_at,
    'updated_at': Organization.updated_at,
}


class OrganizationRepository(SQLAlchemyRepository[Organization, UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def get_by_registration_code(
        self, registration_code: str
    ) -> Organization | None:
        logger.debug(
            f'[{self._model.__name__}] Fetching organization '
            f'by registration_code: {registration_code}'
        )
        stmt = select(Organization).where(
            Organization.registration_code == registration_code
        )
        result = await self._session.execute(stmt)
        organization = result.scalar_one_or_none()
        if organization:
            logger.debug(
                f'[{self._model.__name__}] Found organization '
                f'with registration_code: {registration_code}'
            )
        else:
            logger.debug(
                f'[{self._model.__name__}] Organization with '
                f'registration_code {registration_code} not found'
            )
        return organization

    async def has_linked_entities(self, organization_id: UUID) -> bool:
        logger.debug(
            f'[{self._model.__name__}] Checking linked entities '
            f'for organization_id={organization_id}'
        )

        site_stmt = select(exists().where(Site.land_owner_id == organization_id))
        site_result = await self._session.execute(site_stmt)
        if bool(site_result.scalar()):
            return True

        grid_stmt = select(exists().where(GridConnection.utility_id == organization_id))
        grid_result = await self._session.execute(grid_stmt)
        if bool(grid_result.scalar()):
            return True

        contract_stmt = select(exists().where(Contract.vendor_id == organization_id))
        contract_result = await self._session.execute(contract_stmt)
        if bool(contract_result.scalar()):
            return True

        stage_stmt = select(
            exists().where(
                StageExecution.responsible_organization_id == organization_id
            )
        )
        stage_result = await self._session.execute(stage_stmt)
        if bool(stage_result.scalar()):
            return True

        permit_stmt = select(
            exists().where(Permit.responsible_organization_id == organization_id)
        )
        permit_result = await self._session.execute(permit_stmt)
        if bool(permit_result.scalar()):
            return True

        issue_stmt = select(
            exists().where(Issue.owner_organization_id == organization_id)
        )
        issue_result = await self._session.execute(issue_stmt)
        return bool(issue_result.scalar())

    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        sort: SortParams,
        search: str | None = None,
        organization_kind: OrganizationKind | None = None,
    ) -> tuple[Sequence[Organization], int]:
        logger.debug(
            f'[{self._model.__name__}] Listing organizations '
            f'(limit={limit}, offset={offset}, sort={sort}, '
            f'search={search!r}, organization_kind={organization_kind})'
        )

        filters: list[ColumnElement[bool]] = []

        if organization_kind is not None:
            filters.append(Organization.organization_kind == organization_kind)

        if search is not None:
            escaped = escape_like_pattern(search.strip())
            if escaped:
                pattern = f'%{escaped}%'
                filters.append(
                    or_(
                        Organization.legal_name.ilike(pattern, escape='\\'),
                        Organization.registration_code.ilike(pattern, escape='\\'),
                    )
                )

        count_stmt = select(func.count()).select_from(Organization).where(*filters)
        count_result = await self._session.execute(count_stmt)
        total_items = int(count_result.scalar_one())

        if total_items == 0:
            return [], 0

        sort_column = _ORGANIZATION_SORT_COLUMNS[sort.sort_by]
        primary_order: UnaryExpression[object] = (
            sort_column.asc() if sort.sort_order == 'asc' else sort_column.desc()
        )

        items_stmt = (
            select(Organization)
            .where(*filters)
            .order_by(primary_order, Organization.organization_id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await self._session.execute(items_stmt)
        items = list(items_result.scalars().all())

        logger.debug(
            f'[{self._model.__name__}] Retrieved {len(items)} '
            f'of {total_items} organizations'
        )
        return items, total_items
