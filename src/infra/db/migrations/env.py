import asyncio
import os
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection, URL
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.infra.db.orm.init.file_info_init import Base as FileInfoBase
from src.infra.db.orm.init.user_init import Base as UserBase


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [UserBase.metadata, FileInfoBase.metadata]


def _schema() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    schema = x_args.get('schema') or os.getenv('DB_SCHEMA', 'public').strip()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', schema):
        raise ValueError(f'invalid PostgreSQL schema name: {schema!r}')
    return schema


def _database_url() -> str:
    user = os.getenv('DB_USER', 'user').strip()
    password = os.getenv('DB_PASSWORD', 'pass').strip()
    host = os.getenv('DB_HOST', 'localhost').strip()
    port = os.getenv('DB_PORT', '5432').strip()
    database = os.getenv('DB_NAME', 'postgres').strip()
    return URL.create(
        drivername='postgresql+asyncpg',
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
    ).render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    schema = _schema()
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        include_schemas=True,
        version_table='alembic_version_user',
        version_table_schema=schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    schema = _schema()
    connection.exec_driver_sql(
        f'SET search_path TO "{schema}", public'
    )
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table='alembic_version_user',
        version_table_schema=schema,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {})
    section['sqlalchemy.url'] = _database_url()
    connectable = async_engine_from_config(
        section,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        connect_args=(
            {'ssl': os.getenv('DB_SSL', '').strip()}
            if os.getenv('DB_SSL', '').strip()
            else {}
        ),
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
