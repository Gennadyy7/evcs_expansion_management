import asyncio
from collections.abc import MutableMapping
from typing import Literal

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import settings
from app.core.database import Base
import app.features.core.models
import app.features.pm.models
import app.features.reference.models  # noqa: F401

config = context.config

target_metadata = Base.metadata

SCHEMAS = ('core', 'ref', 'pm')


def include_name(
    name: str | None,
    type_: Literal[
        'schema',
        'table',
        'column',
        'index',
        'unique_constraint',
        'foreign_key_constraint',
        'check_constraint',
    ],
    parent_names: MutableMapping[
        Literal['schema_name', 'table_name', 'schema_qualified_table_name'],
        str | None,
    ],
) -> bool:
    if type_ == 'schema':
        return name in SCHEMAS
    if type_ == 'table':
        return parent_names.get('schema_name') in SCHEMAS
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        settings.DB_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    connectable = context.config.attributes.get('connection', None)
    if connectable is None:
        asyncio.run(run_async_migrations())
    else:
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
