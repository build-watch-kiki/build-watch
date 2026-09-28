from fastapi import APIRouter
from starlette import status

from buildwatch.shared import BaseDetailSchema
from buildwatch.shared.schemas import (
    GanttMetadata,
    MetadataResponse,
    ProjectSearchRequestDep,
    StageGanttRequestDep,
)
from buildwatch.stages.schemas import (
    StageCreate,
    StageResponse,
    StageTechniquesBindRequest,
    StageUpdate,
)
from buildwatch.stages.service import StageServiceDep

router = APIRouter(prefix="/projects/{project_id}/stages", tags=["Этапы проекта"])


@router.get(
    "",
    summary="Получение этапов проекта",
    response_model=BaseDetailSchema[StageResponse, MetadataResponse],
    deprecated=True,
)
async def get_stages(
    project_id: int,
    stage_service: StageServiceDep,
    request: ProjectSearchRequestDep,
):
    """Список этапов проекта (deprecated — используйте /gantt)"""

    stages = await stage_service.get_stages(project_id=project_id, request=request)
    total = await stage_service.get_stages_count(project_id=project_id, request=request)
    return BaseDetailSchema[StageResponse, MetadataResponse](
        items=stages,
        metadata=MetadataResponse(
            total=total, page=request.page, page_size=request.page_size
        ),
    )


@router.get(
    "/gantt",
    summary="Этапы для Ганта (интервал)",
    response_model=BaseDetailSchema[StageResponse, GanttMetadata],
)
async def get_gantt_stages(
    project_id: int,
    stage_service: StageServiceDep,
    request: StageGanttRequestDep,
):
    """Все этапы проекта; from/to, parentId и limit применяются только если заданы."""

    stages = await stage_service.get_gantt_stages(
        project_id=project_id, request=request
    )
    total = await stage_service.get_gantt_stages_count(
        project_id=project_id, request=request
    )
    return BaseDetailSchema[StageResponse, GanttMetadata](
        items=stages,
        metadata=GanttMetadata(total=total, limit=request.limit),
    )


@router.post(
    "",
    summary="Создание этапа проекта",
    status_code=status.HTTP_201_CREATED,
    response_model=int,
)
async def create_stage(
    project_id: int,
    stage_service: StageServiceDep,
    payload: StageCreate,
):
    """Создание этапа в проекте"""

    stage_id = await stage_service.create_stage(project_id=project_id, payload=payload)
    return stage_id


@router.get(
    "/{stage_id}",
    summary="Получение этапа проекта по ID",
    response_model=StageResponse,
)
async def get_stage_by_id(
    project_id: int,
    stage_id: int,
    stage_service: StageServiceDep,
):
    """Этап по идентификатору"""

    stage = await stage_service.get_stage_by_id(
        stage_id=stage_id, project_id=project_id
    )
    return stage


@router.put(
    "/{stage_id}",
    summary="Обновление этапа проекта по ID",
    response_model=StageResponse,
)
async def update_stage_by_id(
    project_id: int,
    stage_id: int,
    stage_service: StageServiceDep,
    payload: StageUpdate,
):
    """Обновление этапа проекта"""

    stage = await stage_service.update_stage(
        stage_id=stage_id, payload=payload, project_id=project_id
    )
    return stage


@router.delete(
    "/{stage_id}",
    summary="Удаление этапа проекта по ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_stage_by_id(
    project_id: int,
    stage_id: int,
    stage_service: StageServiceDep,
):
    """Удаление этапа проекта"""

    await stage_service.delete_stage(stage_id=stage_id, project_id=project_id)
    return None


@router.put(
    "/{stage_id}/techniques",
    summary="Привязка техники к этапу",
    response_model=StageResponse,
)
async def set_stage_techniques(
    project_id: int,
    stage_id: int,
    payload: StageTechniquesBindRequest,
    stage_service: StageServiceDep,
):
    """Полная замена техники этапа с количеством; пустой массив очищает набор."""

    return await stage_service.set_stage_techniques(
        project_id=project_id,
        stage_id=stage_id,
        techniques=payload.techniques,
    )


@router.put(
    "/change-dates/batch",
    summary="Обновление дат этапов стройки",
    deprecated=True,
)
async def update_dates_stages(
    project_id: int,
    stage_service: StageServiceDep,
    payload: StageUpdate,
):
    """Обновление этапа проекта"""

    # @TODO Реализовать батчевое обновление этапов по датам (перемещение родительской задачи двигает другие задачи)
    return
