"""Backfill of active CV runs against an isolated PostgreSQL database."""

import os
import runpy
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from buildwatch.settings import get_settings

pytestmark = pytest.mark.skipif(
    os.getenv("BW_INTEGRATION_TESTS") != "1",
    reason="Set BW_INTEGRATION_TESTS=1 for an isolated PostgreSQL",
)


async def test_migration_backfills_latest_successful_run():
    migration_path = (
        Path(__file__).parents[2]
        / "buildwatch/alembic/versions/2026_09_24_0003-remove_photo_previews.py"
    )
    migration = runpy.run_path(str(migration_path))
    schema_name = f"test_preview_migration_{uuid4().hex}"
    engine = create_async_engine(get_settings().db.POSTGRES_DSN)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
                await connection.execute(
                    text(f'SET LOCAL search_path TO "{schema_name}"')
                )
                await connection.execute(text("""
                    CREATE TABLE cv_runs (
                        id integer PRIMARY KEY,
                        photo_id integer NOT NULL,
                        status text NOT NULL,
                        preview_render_enqueued_at timestamptz
                    )
                    """))
                await connection.execute(text("""
                    CREATE TABLE photos (
                        id integer PRIMARY KEY,
                        is_processed boolean NOT NULL,
                        preview_storage_key varchar(512),
                        preview_cv_run_id integer,
                        CONSTRAINT fk_photos_preview_cv_run_id
                            FOREIGN KEY (preview_cv_run_id)
                            REFERENCES cv_runs(id) ON DELETE SET NULL
                    )
                    """))
                await connection.execute(text("""
                    INSERT INTO cv_runs(id, photo_id, status) VALUES
                        (1, 1, 'succeeded'), (2, 1, 'failed'),
                        (3, 2, 'succeeded'), (4, 3, 'pending'),
                        (5, 4, 'succeeded'), (6, 4, 'succeeded')
                    """))
                await connection.execute(text("""
                    INSERT INTO photos(
                        id, is_processed, preview_storage_key, preview_cv_run_id
                    ) VALUES
                        (1, true, 'old.jpg', 1), (2, false, NULL, NULL),
                        (3, false, NULL, NULL), (4, true, 'older.jpg', 5)
                    """))

                def run_migration(sync_connection, direction):
                    context = MigrationContext.configure(sync_connection)
                    with Operations.context(context):
                        migration[direction]()

                await connection.run_sync(run_migration, "upgrade")
                rows = (await connection.execute(text("""
                        SELECT id, is_processed, active_cv_run_id
                        FROM photos ORDER BY id
                        """))).all()
                assert rows == [
                    (1, True, 1),
                    (2, True, 3),
                    (3, False, None),
                    (4, True, 6),
                ]
                columns = {
                    row[0]
                    for row in (
                        await connection.execute(
                            text("""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_schema = :schema_name
                            """),
                            {"schema_name": schema_name},
                        )
                    ).all()
                }
                assert "preview_storage_key" not in columns
                assert "preview_render_enqueued_at" not in columns
                await connection.run_sync(run_migration, "downgrade")
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
