from fastapi import APIRouter

from buildwatch.projects.schemas import ProjectTypeResponse
from buildwatch.projects.service import ProjectServiceDep
from buildwatch.shared import BaseDetailSchema
from buildwatch.shared.schemas import MetadataResponse, SearchRequestDep
from buildwatch.work_types.schemas import WorkTypeResponse
from buildwatch.work_types.service import WorkTypesServiceDep

router = APIRouter(tags=["Справочники типов работ/проектов"])


@router.get(
    "/work-types",
    summary="Получение доступных типов строительных работ",
    response_model=BaseDetailSchema[WorkTypeResponse],
)
async def get_work_types(
    work_types_service: WorkTypesServiceDep, request: SearchRequestDep
):
    """Список типов строительных работ"""

    items = await work_types_service.get_work_types(request)
    count = await work_types_service.get_work_types_count(request)
    return BaseDetailSchema(
        items=items,
        metadata=MetadataResponse(
            total=count, page=request.page, page_size=request.page_size
        ),
    )


@router.get(
    "/project-types",
    summary="Получение возможных типов проектов",
    response_model=BaseDetailSchema[ProjectTypeResponse],
)
async def get_project_types(
    project_service: ProjectServiceDep,
    request: SearchRequestDep,
):
    """Список типов проектов с поиском и пагинацией"""

    projects_types = await project_service.get_project_types(request=request)
    projects_types_count = await project_service.get_project_types_count(
        request=request
    )
    return BaseDetailSchema(
        items=projects_types,
        metadata=MetadataResponse(
            total=projects_types_count, page=request.page, page_size=request.page_size
        ),
    )
