"""Repository checks against an isolated PostgreSQL with migrations applied."""

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from buildwatch.infrastructure.database.models import (
    ProjectTypesORM,
    ProjectsORM,
    StageTechniquesORM,
    StagesORM,
    TechniquesORM,
    WorkTypesORM,
)
from buildwatch.photos.repository import PhotosRepository
from buildwatch.stages.repository import StagesRepository
from buildwatch.stages.schemas import StageResponse
from buildwatch.stages.specifications import LoadTechniques, LoadWorkType
from buildwatch.stages.specifications import StageWorkTypeNameSpec
from buildwatch.settings import get_settings

pytestmark = pytest.mark.skipif(
    os.getenv("BW_INTEGRATION_TESTS") != "1",
    reason="Set BW_INTEGRATION_TESTS=1 for an isolated, migrated PostgreSQL",
)


async def test_technique_replacement_and_photo_pagination():
    engine = create_async_engine(get_settings().db.POSTGRES_DSN, poolclass=NullPool)
    try:
        await _check_repositories(async_sessionmaker(engine, expire_on_commit=False))
    finally:
        await engine.dispose()


async def _check_repositories(session_maker):
    date_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    date_end = datetime(2026, 12, 31, tzinfo=timezone.utc)
    async with session_maker() as session:
        project_type = ProjectTypesORM(name="Integration")
        work_type = WorkTypesORM(name="Integration")
        technique_a = TechniquesORM(
            name="excavator", name_ru="Экскаватор", color="#0080FF"
        )
        technique_b = TechniquesORM(name="crane", name_ru="Кран", color="#00FFC9")
        project = ProjectsORM(
            name="Internal name is ignored",
            type=project_type,
            start_dt=date_start,
            end_dt=date_end,
        )
        stage = StagesORM(
            project=project,
            work_type=work_type,
            name="Integration",
            start_dt=date_start,
            end_dt=date_end,
        )
        session.add_all((stage, technique_a, technique_b))
        await session.flush()

        stages_repo = StagesRepository(session)
        await stages_repo.set_stage_techniques(
            stage.id, [(technique_a.id, 2), (technique_b.id, 4)]
        )
        await stages_repo.set_stage_techniques(stage.id, [(technique_b.id, 5)])
        links = (
            (
                await session.execute(
                    select(StageTechniquesORM).where(
                        StageTechniquesORM.stage_id == stage.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert [(link.technique_id, link.quantity) for link in links] == [
            (technique_b.id, 5)
        ]
        loaded_stage = await stages_repo.get_stage_by_id(
            stage.id, LoadWorkType(), LoadTechniques()
        )
        assert StageResponse.model_validate(loaded_stage).techniques[0].quantity == 5
        response_stage = StageResponse.model_validate(loaded_stage).model_dump(
            by_alias=True
        )
        assert response_stage["workTypeName"] == "Integration"
        assert response_stage["workTypeId"] == work_type.id
        assert "name" not in response_stage and "workType" not in response_stage
        matching = StageWorkTypeNameSpec("integration")
        assert len(await stages_repo.get_stages(matching, project_id=project.id)) == 1
        assert (
            await stages_repo.get_count(StagesORM, matching, project_id=project.id) == 1
        )
        missing = StageWorkTypeNameSpec("not-in-work-type")
        assert len(await stages_repo.get_stages(missing, project_id=project.id)) == 0
        assert (
            await stages_repo.get_count(StagesORM, missing, project_id=project.id) == 0
        )

        photos_repo = PhotosRepository(session)
        unique = uuid4().hex
        await photos_repo.create_photo(
            project.id,
            f"{project.id}/photos/{unique}/old.jpg",
            date_start,
            640,
            480,
            "JPEG",
        )
        await photos_repo.create_photo(
            project.id,
            f"{project.id}/photos/{unique}/new.jpg",
            date_end,
            1920,
            1080,
            "JPEG",
            is_processed=True,
        )
        await photos_repo.create_photo(
            project.id,
            f"{project.id}/photos/{unique}/undated.jpg",
            None,
            None,
            None,
            None,
        )
        assert await photos_repo.count_photos(project.id) == 3
        assert await photos_repo.count_photos(project.id, is_processed=True) == 1
        assert await photos_repo.count_photos(project.id, is_processed=False) == 2
        processed = await photos_repo.list_photos(
            project.id, limit=10, offset=0, is_processed=True
        )
        assert [photo.storage_key.rsplit("/", 1)[-1] for photo in processed] == [
            "new.jpg"
        ]
        unprocessed = await photos_repo.list_photos(
            project.id, limit=10, offset=0, is_processed=False
        )
        assert [photo.storage_key.rsplit("/", 1)[-1] for photo in unprocessed] == [
            "old.jpg",
            "undated.jpg",
        ]
        first = await photos_repo.list_photos(project.id, limit=1, offset=0)
        assert first[0].storage_key.endswith("new.jpg")
        page = await photos_repo.list_photos(project.id, limit=1, offset=1)
        assert len(page) == 1
        assert page[0].storage_key.endswith("old.jpg")
        last = await photos_repo.list_photos(project.id, limit=1, offset=2)
        assert last[0].storage_key.endswith("undated.jpg")

        await stages_repo.set_stage_techniques(stage.id, [])
        assert (
            await session.execute(
                select(StageTechniquesORM).where(
                    StageTechniquesORM.stage_id == stage.id
                )
            )
        ).scalars().all() == []
        await session.rollback()
