from collections.abc import AsyncGenerator, Callable

from app.core.database import db_manager
from app.core.unit_of_work.protocol import UnitOfWorkProtocol
from app.core.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


def get_unit_of_work_factory(
    uow_factory: Callable[[], AsyncGenerator[UnitOfWorkProtocol]],
) -> Callable[[], AsyncGenerator[UnitOfWorkProtocol]]:
    return uow_factory


async def provide_sqlalchemy_uow() -> AsyncGenerator[UnitOfWorkProtocol]:
    async with SQLAlchemyUnitOfWork(db_manager.session_factory) as uow:
        yield uow


get_uow = get_unit_of_work_factory(provide_sqlalchemy_uow)
