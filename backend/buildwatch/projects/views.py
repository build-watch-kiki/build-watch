from http.client import responses

from fastapi import APIRouter
from starlette import status

from buildwatch.projects.schemas import ProjectCreate, ProjectUpdate
from buildwatch.projects.schemas import ProjectResponse
from buildwatch.projects.service import ProjectServiceDep
from buildwatch.shared import BaseDetailSchema, PaginationDep
from buildwatch.shared.schemas import MetadataResponse, SearchRequestDep
from buildwatch.work_types.schemas import WorkTypeResponse
from buildwatch.work_types.service import WorkTypesServiceDep

router = APIRouter(prefix="/projects", tags=["Проекты (рабочие объекты) 🏘️"])


@router.get(
    "", summary="Получение проектов", response_model=BaseDetailSchema[ProjectResponse]
)
async def get_projects(project_service: ProjectServiceDep, pagination: PaginationDep):
    """Список проектов с пагинацией"""

    projects = await project_service.get_projects(pagination)
    count = await project_service.get_projects_count()
    return BaseDetailSchema(
        items=projects,
        metadata=MetadataResponse(
            total=count, page=pagination.page, page_size=pagination.page_size
        ),
    )


@router.post(
    "",
    summary="Создание проекта",
    status_code=status.HTTP_201_CREATED,
    response_model=int,
)
async def create_project(project_service: ProjectServiceDep, payload: ProjectCreate):
    """Создание нового проекта"""

    project_id = await project_service.create_project(payload)
    return project_id


@router.get(
    "/{project_id}",
    summary="Получение проекта по ID",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: int,
    project_service: ProjectServiceDep,
):
    """Проект по идентификатору"""

    return await project_service.get_project(project_id)


@router.put(
    "/{project_id}",
    summary="Обновление проекта по ID",
    response_model=ProjectResponse,
)
async def update_project(
        project_id: int,
        project_service: ProjectServiceDep,
        payload: ProjectUpdate,
):
    """Обновление проекта"""

    project = await project_service.update_project(
        project_id=project_id, payload=payload
    )
    return project


@router.delete(
    "/{project_id}",
    summary="Удаление проекта по ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    project_service: ProjectServiceDep,
):
    """Удаление проекта по идентификатору"""

    await project_service.delete_project(project_id)


@router.get(
    "/{project_id}/work-types",
    summary="Доступные типы работ для проекта (по типу проекта)",
    response_model=BaseDetailSchema[WorkTypeResponse],
)
async def get_available_work_types(
    project_id: int,
    work_types_service: WorkTypesServiceDep,
    request: SearchRequestDep,
):
    """Типы работ, доступные для конкретного проекта"""

    items = await work_types_service.get_available_for_project(
        project_id=project_id, request=request
    )
    total = await work_types_service.get_available_for_project_count(
        project_id=project_id, request=request
    )
    return BaseDetailSchema(
        items=items,
        metadata=MetadataResponse(
            total=total, page=request.page, page_size=request.page_size
        ),
    )
