"""Convert User-owned PostgreSQL enums to varchar/check constraints.

Revision ID: 20260620_0002
Revises: 20260620_0001
Create Date: 2026-06-20
"""
import os
from typing import Sequence, Union

from alembic import context, op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql


revision: str = '20260620_0002'
down_revision: Union[str, None] = '20260620_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CHECKS = {
    'profiles': {
        'ck_profiles_seniority_level': (
            "seniority_level IN "
            "('NO REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER')"
        ),
    },
    'mentor_schedules': {
        'ck_mentor_schedules_dt_type': (
            "dt_type IN ('ALLOW', 'FORBIDDEN')"
        ),
    },
    'canned_messages': {
        'ck_canned_messages_role': (
            "role IN ('MENTOR', 'MENTEE')"
        ),
    },
    'reservations': {
        'ck_reservations_my_status': (
            "my_status IN ('ACCEPT', 'PENDING', 'REJECT')"
        ),
        'ck_reservations_my_role': (
            "my_role IS NULL OR my_role IN ('MENTOR', 'MENTEE')"
        ),
        'ck_reservations_status': (
            "status IN ('ACCEPT', 'PENDING', 'REJECT')"
        ),
    },
    'interests': {
        'ck_interests_category': (
            "category IS NULL OR category IN "
            "('INTERESTED_POSITION', 'SKILL', 'TOPIC')"
        ),
    },
    'activities': {
        'ck_activities_service': "service IN ('GOOGLE')",
        'ck_activities_status': (
            "status IN ('SCHEDULED', 'CANCELLED')"
        ),
    },
}

ENUM_COLUMNS = (
    ('profiles', 'seniority_level', 'VARCHAR(20)'),
    ('canned_messages', 'role', 'VARCHAR(20)'),
    ('reservations', 'my_status', 'VARCHAR(20)'),
    ('reservations', 'my_role', 'VARCHAR(20)'),
    ('reservations', 'status', 'VARCHAR(20)'),
    ('interests', 'category', 'VARCHAR(40)'),
    ('activities', 'service', 'VARCHAR(20)'),
    ('activities', 'status', 'VARCHAR(20)'),
)

OWNED_ENUMS = (
    'seniority_level',
    'interest_category',
    'experience_category',
    'schedule_type',
    'booking_status',
    'role_type',
    'industry_category',
    'activity_service',
    'activity_status',
)


def _drop_reservation_indexes(bind) -> None:
    schema = _quoted_schema(bind)
    for index_name in (
        'uidx_reservation_active_user_dtstart_dtend_schedule_id_user_id',
        'idx_reservation_user_my_status_status_dtend',
        'idx_reservation_user_my_status_dtstart_dtend',
    ):
        bind.execute(text(
            f'DROP INDEX IF EXISTS {schema}."{index_name}"'
        ))


def _create_reservation_indexes(bind) -> None:
    inspector = inspect(bind)
    if not _table_exists(inspector, 'reservations'):
        return
    schema = _quoted_schema(bind)
    bind.execute(text(
        'CREATE UNIQUE INDEX IF NOT EXISTS '
        'uidx_reservation_active_user_dtstart_dtend_schedule_id_user_id '
        f'ON {schema}.reservations '
        '(my_user_id, dtstart, dtend, schedule_id, user_id) '
        "WHERE my_status <> 'REJECT' AND status <> 'REJECT'"
    ))
    bind.execute(text(
        'CREATE INDEX IF NOT EXISTS '
        'idx_reservation_user_my_status_status_dtend '
        f'ON {schema}.reservations '
        '(my_user_id, my_status, status, dtend)'
    ))
    bind.execute(text(
        'CREATE INDEX IF NOT EXISTS '
        'idx_reservation_user_my_status_dtstart_dtend '
        f'ON {schema}.reservations '
        '(my_user_id, my_status, dtstart, dtend)'
    ))


def _drop_activity_defaults(bind) -> None:
    inspector = inspect(bind)
    if not _table_exists(inspector, 'activities'):
        return
    schema = _quoted_schema(bind)
    bind.execute(text(
        f'ALTER TABLE {schema}.activities '
        'ALTER COLUMN service DROP DEFAULT, '
        'ALTER COLUMN status DROP DEFAULT'
    ))


def _set_string_activity_defaults(bind) -> None:
    inspector = inspect(bind)
    if not _table_exists(inspector, 'activities'):
        return
    schema = _quoted_schema(bind)
    bind.execute(text(
        f'ALTER TABLE {schema}.activities '
        "ALTER COLUMN service SET DEFAULT 'GOOGLE', "
        "ALTER COLUMN status SET DEFAULT 'SCHEDULED'"
    ))


def _set_enum_activity_defaults(bind) -> None:
    inspector = inspect(bind)
    if not _table_exists(inspector, 'activities'):
        return
    schema = _quoted_schema(bind)
    bind.execute(text(
        f'ALTER TABLE {schema}.activities '
        f"ALTER COLUMN service SET DEFAULT 'GOOGLE'::{schema}.activity_service, "
        f"ALTER COLUMN status SET DEFAULT 'SCHEDULED'::{schema}.activity_status"
    ))


def _schema() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    return x_args.get('schema') or os.getenv('DB_SCHEMA', 'public').strip()


def _quoted_schema(bind) -> str:
    return bind.dialect.identifier_preparer.quote_schema(_schema())


def _table_exists(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name, schema=_schema())


def _column(inspector, table_name: str, column_name: str):
    if not _table_exists(inspector, table_name):
        return None
    return next(
        (
            column
            for column in inspector.get_columns(table_name, schema=_schema())
            if column['name'] == column_name
        ),
        None,
    )


def _convert_enum_column(
    bind,
    inspector,
    table_name: str,
    column_name: str,
    target_type: str,
) -> None:
    column = _column(inspector, table_name, column_name)
    if column is None or not isinstance(column['type'], postgresql.ENUM):
        return

    schema = _quoted_schema(bind)
    using_expression = f'{column_name}::text'
    if table_name == 'profiles' and column_name == 'seniority_level':
        using_expression = (
            "CASE WHEN seniority_level::text = 'NO_REVEAL' "
            "THEN 'NO REVEAL' ELSE seniority_level::text END"
        )

    bind.execute(text(
        f'ALTER TABLE {schema}."{table_name}" '
        f'ALTER COLUMN "{column_name}" TYPE {target_type} '
        f'USING ({using_expression})'
    ))


def _add_checks(bind) -> None:
    inspector = inspect(bind)
    schema = _quoted_schema(bind)
    for table_name, constraints in CHECKS.items():
        if not _table_exists(inspector, table_name):
            continue
        existing = {
            constraint['name']
            for constraint in inspector.get_check_constraints(
                table_name,
                schema=_schema(),
            )
        }
        for constraint_name, condition in constraints.items():
            if constraint_name in existing:
                continue
            bind.execute(text(
                f'ALTER TABLE {schema}."{table_name}" '
                f'ADD CONSTRAINT "{constraint_name}" CHECK ({condition})'
            ))


def _drop_checks(bind) -> None:
    inspector = inspect(bind)
    schema = _quoted_schema(bind)
    for table_name, constraints in CHECKS.items():
        if not _table_exists(inspector, table_name):
            continue
        existing = {
            constraint['name']
            for constraint in inspector.get_check_constraints(
                table_name,
                schema=_schema(),
            )
        }
        for constraint_name in constraints:
            if constraint_name not in existing:
                continue
            bind.execute(text(
                f'ALTER TABLE {schema}."{table_name}" '
                f'DROP CONSTRAINT "{constraint_name}"'
            ))


def _ensure_profile_storage_shape(bind) -> None:
    inspector = inspect(bind)
    if not _table_exists(inspector, 'profiles'):
        return
    schema = _quoted_schema(bind)
    if _column(inspector, 'profiles', 'linkedin_profile') is None:
        bind.execute(text(
            f'ALTER TABLE {schema}.profiles '
            "ADD COLUMN linkedin_profile TEXT DEFAULT ''"
        ))

    for column_name in (
        'name',
        'avatar',
        'location',
        'job_title',
        'company',
        'industry',
    ):
        if _column(inspector, 'profiles', column_name) is not None:
            bind.execute(text(
                f'ALTER TABLE {schema}.profiles '
                f'ALTER COLUMN "{column_name}" TYPE TEXT'
            ))

    if _column(inspector, 'profiles', 'years_of_experience') is not None:
        bind.execute(text(
            f'ALTER TABLE {schema}.profiles '
            'ALTER COLUMN years_of_experience TYPE VARCHAR'
        ))


def _create_enum_types(bind) -> None:
    schema = _quoted_schema(bind)
    enum_definitions = {
        'seniority_level': (
            "'NO_REVEAL', 'JUNIOR', 'INTERMEDIATE', 'SENIOR', 'STAFF', 'MANAGER'"
        ),
        'interest_category': "'INTERESTED_POSITION', 'SKILL', 'TOPIC'",
        'experience_category': "'WORK', 'EDUCATION', 'LINK', 'WHAT_I_OFFER'",
        'schedule_type': "'ALLOW', 'FORBIDDEN'",
        'booking_status': "'ACCEPT', 'PENDING', 'REJECT'",
        'role_type': "'MENTOR', 'MENTEE'",
        'industry_category': "'SOFTWARE', 'HARDWARE', 'SERVICE', 'FINANCE', 'OTHER'",
        'activity_service': "'GOOGLE'",
        'activity_status': "'SCHEDULED', 'CANCELLED'",
    }
    for enum_name, values in enum_definitions.items():
        bind.execute(text(
            'DO $$ BEGIN '
            f'CREATE TYPE {schema}."{enum_name}" AS ENUM ({values}); '
            'EXCEPTION WHEN duplicate_object THEN NULL; '
            'END $$'
        ))


def _restore_enum_column(
    bind,
    inspector,
    table_name: str,
    column_name: str,
    enum_name: str,
) -> None:
    column = _column(inspector, table_name, column_name)
    if column is None or isinstance(column['type'], postgresql.ENUM):
        return
    schema = _quoted_schema(bind)
    expression = f'"{column_name}"::text'
    if table_name == 'profiles' and column_name == 'seniority_level':
        expression = (
            "CASE WHEN seniority_level = 'NO REVEAL' "
            "THEN 'NO_REVEAL' ELSE seniority_level END"
        )
    bind.execute(text(
        f'ALTER TABLE {schema}."{table_name}" '
        f'ALTER COLUMN "{column_name}" TYPE {schema}."{enum_name}" '
        f'USING ({expression})::{schema}."{enum_name}"'
    ))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _ensure_profile_storage_shape(bind)
    _drop_reservation_indexes(bind)
    _drop_activity_defaults(bind)
    inspector = inspect(bind)
    for table_name, column_name, target_type in ENUM_COLUMNS:
        _convert_enum_column(
            bind,
            inspector,
            table_name,
            column_name,
            target_type,
        )

    _add_checks(bind)
    _set_string_activity_defaults(bind)
    _create_reservation_indexes(bind)

    schema = _quoted_schema(bind)
    for enum_name in OWNED_ENUMS:
        bind.execute(text(
            f'DROP TYPE IF EXISTS {schema}."{enum_name}"'
        ))


def downgrade() -> None:
    bind = op.get_bind()
    _drop_checks(bind)
    _drop_reservation_indexes(bind)
    _drop_activity_defaults(bind)
    _create_enum_types(bind)

    inspector = inspect(bind)
    for table_name, column_name, enum_name in (
        ('profiles', 'seniority_level', 'seniority_level'),
        ('canned_messages', 'role', 'role_type'),
        ('reservations', 'my_status', 'booking_status'),
        ('reservations', 'my_role', 'role_type'),
        ('reservations', 'status', 'booking_status'),
        ('interests', 'category', 'interest_category'),
        ('activities', 'service', 'activity_service'),
        ('activities', 'status', 'activity_status'),
    ):
        _restore_enum_column(
            bind,
            inspector,
            table_name,
            column_name,
            enum_name,
        )

    _set_enum_activity_defaults(bind)
    _create_reservation_indexes(bind)
