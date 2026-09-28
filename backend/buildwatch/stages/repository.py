import logging
from typing import Sequence, Any, Annotated

from fastapi import Depends
from sqlalchemy import delete

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models import StagesORM
from buildwatch.infrastructure.database.models.core.techniques import StageTechniquesORM
from buildwatch.settings import get_settings
from buildwatch.shared.repository import SQLBaseRepository
from buildwatch.stages.contracts import StagesRepositoryProtocol
from buildwatch.stages.mock import MockStageRepository

logger = logging.getLogger(__name__)

settings = get_settings()


class StagesRepository(SQLBaseRepository, StagesRepositoryProtocol):
    """Реализация репозитория этапов"""

    async def create_stage(
        self,
        project_id: int,
        parent_id: int | None,
        work_type_id: int,
        name: str,
        start_dt: Any,
        end_dt: Any,
    ) -> int:
        """Создание этапа проекта"""

        logger.debug("Creating stage: %s", name)
        stage = StagesORM(
            project_id=project_id,
            parent_id=parent_id,
            work_type_id=work_type_id,
            name=name,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        self.session.add(stage)
        await self.session.flush()
        logger.debug("Stage created with id: %d", stage.id)
        return stage.id

    async def get_stages(self, *specs: Any, **filter_by: Any) -> Sequence[StagesORM]:
        """Список этапов по фильтрам"""

        logger.debug("Getting stages with filter: %s", filter_by)
        return await self.get_all(StagesORM, *specs, **filter_by)

    async def get_stage_by_id(self, stage_id: int, *specs: Any) -> StagesORM | None:
        """Этап по идентификатору"""

        logger.debug("Getting stage by id: %d", stage_id)
        return await self.get_one(StagesORM, *specs, id=stage_id)

    async def update_stage(self, stage_id: int, **kwargs: Any) -> None:
        """Обновление полей этапа"""

        logger.debug("Updating stage: %d", stage_id)
        stage = await self.get_one(StagesORM, id=stage_id)
        if stage is None:
            return
        for key, value in kwargs.items():
            setattr(stage, key, value)
        await self.session.flush()

    async def delete_stage(self, stage_id: int) -> None:
        """Удаление этапа"""

        logger.debug("Deleting stage: %d", stage_id)
        stage = await self.get_one(StagesORM, id=stage_id)
        if stage is None:
            return
        await self.session.delete(stage)
        await self.session.flush()

    async def get_count(self, model: Any, *specs: Any, **filter_by: Any) -> int:
        """Подсчет этапов по фильтрам"""

        return await super().get_count(model, *specs, **filter_by)

    async def set_stage_techniques(
        self, stage_id: int, techniques: list[tuple[int, int]]
    ) -> None:
        """Замена техники этапа — удаление всех старых + вставка новых"""

        logger.debug("Setting techniques for stage %d: %s", stage_id, techniques)
        await self.session.execute(
            delete(StageTechniquesORM).where(StageTechniquesORM.stage_id == stage_id)
        )
        for technique_id, quantity in techniques:
            self.session.add(
                StageTechniquesORM(
                    stage_id=stage_id, technique_id=technique_id, quantity=quantity
                )
            )
        await self.session.flush()
        stage = await self.session.get(StagesORM, stage_id)
        if stage is not None:
            self.session.expire(stage, ["technique_links"])


def get_stage_repository(session: SessionDep) -> StagesRepositoryProtocol:
    if settings.use_mock.stage_repo:
        return MockStageRepository()
    return StagesRepository(session)


StagesRepositoryDep = Annotated[StagesRepository, Depends(get_stage_repository)]
