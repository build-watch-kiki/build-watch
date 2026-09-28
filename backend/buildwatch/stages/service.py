from typing import Annotated

from fastapi import Depends

from buildwatch.infrastructure.database.manager import DBManager, DBManagerDep
from buildwatch.infrastructure.database.models import StagesORM
from buildwatch.infrastructure.database.models.core.techniques import TechniquesORM
from buildwatch.infrastructure.database.specifications import (
    DateRangeSpec,
    IntervalOverlapSpec,
    InSpec,
    LimitOffsetSpec,
    OrderBySpec,
)
from buildwatch.progress.messages import stage_message, status_from_timing
from buildwatch.progress.schemas import StageActualProgressResponse
from buildwatch.shared.exceptions import BuildWatchException, NotFoundException
from buildwatch.shared.schemas import ProjectSearchRequest, StageGanttRequest
from buildwatch.stages.schemas import (
    StageCreate,
    StageResponse,
    StageTechniqueRequest,
    StageUpdate,
)
from buildwatch.stages.specifications import (
    LoadWorkType,
    LoadTechniques,
    StageWorkTypeNameSpec,
)


class StageService:
    """Бизнес-логика этапов строительства"""

    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def get_stages(
        self, project_id: int, request: ProjectSearchRequest
    ) -> list[StageResponse]:
        """Список этапов проекта с пагинацией"""

        stages = await self.db_manager.stage_repo.get_stages(
            LoadWorkType(),
            LoadTechniques(),
            LimitOffsetSpec(
                limit=request.page_size,
                offset=max(0, (request.page - 1) * request.page_size),
            ),
            StageWorkTypeNameSpec(request.search),
            DateRangeSpec(
                start_col=StagesORM.start_dt,
                end_col=StagesORM.end_dt,
                start_date=request.start_dt,
                end_date=request.end_dt,
            ),
            project_id=project_id,
        )
        return [StageResponse.model_validate(stage) for stage in stages]

    async def get_stages_count(
        self, project_id: int, request: ProjectSearchRequest
    ) -> int:
        """Общее количество этапов проекта"""

        return await self.db_manager.stage_repo.get_count(
            StagesORM,
            StageWorkTypeNameSpec(request.search),
            DateRangeSpec(
                start_col=StagesORM.start_dt,
                end_col=StagesORM.end_dt,
                start_date=request.start_dt,
                end_date=request.end_dt,
            ),
            project_id=project_id,
        )

    async def get_gantt_stages(
        self, project_id: int, request: StageGanttRequest
    ) -> list[StageResponse]:
        """Этапы проекта с необязательными фильтрами и лимитом."""

        filter_kwargs: dict = {"project_id": project_id}
        if request.parent_id is not None:
            filter_kwargs["parent_id"] = request.parent_id

        specs: list = [
            LoadWorkType(),
            LoadTechniques(),
            IntervalOverlapSpec(
                start_col=StagesORM.start_dt,
                end_col=StagesORM.end_dt,
                from_date=request.from_dt,
                to_date=request.to_dt,
            ),
            OrderBySpec(StagesORM.start_dt),
        ]
        if request.limit is not None:
            specs.append(LimitOffsetSpec(limit=request.limit, offset=0))

        stages = await self.db_manager.stage_repo.get_stages(
            *specs,
            **filter_kwargs,
        )
        progress = await self.db_manager.list_gantt_progress(
            project_id, request.from_dt, request.to_dt
        )
        actual_by_stage = {
            item.stage_id: self._actual_progress(item) for item in progress
        }
        return [
            StageResponse.model_validate(stage).model_copy(
                update={"actual": actual_by_stage.get(stage.id)}
            )
            for stage in stages
        ]

    @staticmethod
    def _actual_progress(snapshot) -> StageActualProgressResponse:
        progress = snapshot.progress
        status = status_from_timing(progress.timing_status)
        technique_deviation_count = sum(row.is_deviation for row in progress.techniques)
        return StageActualProgressResponse(
            start_date=snapshot.start_date,
            end_date=snapshot.end_date,
            status=status,
            deviation_days=(
                None if status == "unknown" else progress.time_deviation_days
            ),
            technique_deviation_count=technique_deviation_count,
            message=stage_message(
                status,
                progress.actual_stage_name,
                progress.time_deviation_days,
                technique_deviation_count,
                compact=True,
            ),
        )

    async def get_gantt_stages_count(
        self, project_id: int, request: StageGanttRequest
    ) -> int:
        filters = {"project_id": project_id}
        if request.parent_id is not None:
            filters["parent_id"] = request.parent_id
        return await self.db_manager.stage_repo.get_count(
            StagesORM,
            IntervalOverlapSpec(
                start_col=StagesORM.start_dt,
                end_col=StagesORM.end_dt,
                from_date=request.from_dt,
                to_date=request.to_dt,
            ),
            **filters,
        )

    async def _resolve_techniques(
        self, requirements: list[StageTechniqueRequest]
    ) -> list[tuple[int, int]]:
        names = [item.name for item in requirements]
        if len(names) != len(set(names)):
            raise BuildWatchException(detail="Дубли техники в запросе", status_code=400)
        if not names:
            return []
        techniques = await self.db_manager.technique_repo.get_techniques(
            InSpec(TechniquesORM.name, names)
        )
        by_name = {technique.name: technique.id for technique in techniques}
        missing = set(names) - by_name.keys()
        if missing:
            raise NotFoundException(f"Техника не найдена: {', '.join(sorted(missing))}")
        return [(by_name[item.name], item.quantity) for item in requirements]

    async def create_stage(self, project_id: int, payload: StageCreate) -> int:
        """Создание этапа с проверкой проекта, типа работ и опциональной привязкой техники"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")

        work_type = await self.db_manager.work_type_repo.get_work_type_by_id(
            payload.work_type_id
        )
        if work_type is None:
            raise NotFoundException(f"Тип работ с id {payload.work_type_id} не найден")

        if payload.parent_id is not None:
            parent_stage = await self.db_manager.stage_repo.get_stage_by_id(
                payload.parent_id
            )
            if parent_stage is None or parent_stage.project_id != project_id:
                raise NotFoundException(
                    f"Родительский этап с id {payload.parent_id} не найден в проекте {project_id}"
                )

        technique_requirements = await self._resolve_techniques(payload.techniques)

        stage_id = await self.db_manager.stage_repo.create_stage(
            project_id=project_id,
            parent_id=payload.parent_id,
            work_type_id=payload.work_type_id,
            name=work_type.name,
            start_dt=payload.start_dt,
            end_dt=payload.end_dt,
        )
        # flush уже внутри репо, теперь привязываем технику если нужно
        if technique_requirements:
            await self.db_manager.stage_repo.set_stage_techniques(
                stage_id, technique_requirements
            )
        await self.db_manager.recalculate_progress(project_id)
        await self.db_manager.commit()
        return stage_id

    async def get_stage_by_id(
        self, stage_id: int, project_id: int | None = None
    ) -> StageResponse:
        """Этап по идентификатору с опциональной проверкой принадлежности к проекту"""

        stage = await self.db_manager.stage_repo.get_stage_by_id(
            stage_id, LoadWorkType(), LoadTechniques()
        )
        if stage is None:
            raise NotFoundException(f"Этап с id {stage_id} не найден")
        if project_id is not None and stage.project_id != project_id:
            raise NotFoundException(
                f"Этап с id {stage_id} не найден в проекте {project_id}"
            )
        return StageResponse.model_validate(stage)

    async def update_stage(
        self, stage_id: int, payload: StageUpdate, project_id: int | None = None
    ) -> StageResponse:
        """Обновление этапа по идентификатору"""

        stage = await self.db_manager.stage_repo.get_stage_by_id(stage_id)
        if stage is None:
            raise NotFoundException(f"Этап с id {stage_id} не найден")
        if project_id is not None and stage.project_id != project_id:
            raise NotFoundException(
                f"Этап с id {stage_id} не найден в проекте {project_id}"
            )

        update_data = payload.model_dump(exclude_unset=True)
        if payload.work_type_id is not None:
            work_type = await self.db_manager.work_type_repo.get_work_type_by_id(
                payload.work_type_id
            )
            if work_type is None:
                raise NotFoundException(
                    f"Тип работ с id {payload.work_type_id} не найден"
                )
            update_data["name"] = work_type.name
        await self.db_manager.stage_repo.update_stage(stage_id, **update_data)
        await self.db_manager.recalculate_progress(stage.project_id)
        await self.db_manager.commit()
        return StageResponse.model_validate(
            await self.db_manager.stage_repo.get_stage_by_id(
                stage_id, LoadWorkType(), LoadTechniques()
            )
        )

    async def delete_stage(self, stage_id: int, project_id: int | None = None) -> None:
        """Удаление этапа по идентификатору"""

        stage = await self.db_manager.stage_repo.get_stage_by_id(stage_id)
        if stage is None:
            raise NotFoundException(f"Этап с id {stage_id} не найден")
        if project_id is not None and stage.project_id != project_id:
            raise NotFoundException(
                f"Этап с id {stage_id} не найден в проекте {project_id}"
            )
        await self.db_manager.stage_repo.delete_stage(stage_id)
        await self.db_manager.recalculate_progress(stage.project_id)
        await self.db_manager.commit()

    async def set_stage_techniques(
        self,
        project_id: int,
        stage_id: int,
        techniques: list[StageTechniqueRequest],
    ) -> StageResponse:
        """Полная замена техники этапа с требуемым количеством."""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")

        stage = await self.db_manager.stage_repo.get_stage_by_id(stage_id)
        if stage is None:
            raise NotFoundException(f"Этап с id {stage_id} не найден")
        if stage.project_id != project_id:
            raise NotFoundException(
                f"Этап с id {stage_id} не найден в проекте {project_id}"
            )

        requirements = await self._resolve_techniques(techniques)
        await self.db_manager.stage_repo.set_stage_techniques(stage_id, requirements)
        await self.db_manager.recalculate_progress(project_id)
        await self.db_manager.commit()
        return StageResponse.model_validate(
            await self.db_manager.stage_repo.get_stage_by_id(
                stage_id, LoadWorkType(), LoadTechniques()
            )
        )


def get_stage_service(db_manager: DBManagerDep):
    return StageService(db_manager)


StageServiceDep = Annotated[StageService, Depends(get_stage_service)]
