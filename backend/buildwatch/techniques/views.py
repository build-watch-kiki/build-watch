from fastapi import APIRouter
from starlette import status

from buildwatch.shared import BaseDetailSchema
from buildwatch.shared.schemas import MetadataResponse, SearchRequestDep
from buildwatch.techniques.schemas import (
    TechniqueResponse,
    TechniqueCreate,
    TechniqueUpdate,
)
from buildwatch.techniques.service import TechniqueServiceDep

router = APIRouter(prefix="/techniques", tags=["Техника"])


@router.get(
    "",
    summary="Получение списка техники",
    response_model=BaseDetailSchema[TechniqueResponse],
)
async def get_techniques(
    technique_service: TechniqueServiceDep, request: SearchRequestDep
):
    """Список техники"""
    items = await technique_service.get_techniques(request)
    count = await technique_service.get_techniques_count(request)
    return BaseDetailSchema(
        items=items,
        metadata=MetadataResponse(
            total=count, page=request.page, page_size=request.page_size
        ),
    )


@router.post(
    "",
    summary="Создание техники",
    status_code=status.HTTP_201_CREATED,
    response_model=int,
)
async def create_technique(
    technique_service: TechniqueServiceDep, payload: TechniqueCreate
):
    """Создание техники"""
    return await technique_service.create_technique(payload)


@router.get(
    "/{technique_id}",
    summary="Получение техники по ID",
    response_model=TechniqueResponse,
)
async def get_technique_by_id(
    technique_id: int, technique_service: TechniqueServiceDep
):
    """Техника по идентификатору"""
    return await technique_service.get_technique_by_id(technique_id)


@router.put(
    "/{technique_id}",
    summary="Обновление техники",
    response_model=TechniqueResponse,
)
async def update_technique(
    technique_id: int,
    technique_service: TechniqueServiceDep,
    payload: TechniqueUpdate,
):
    """Обновление техники"""
    return await technique_service.update_technique(technique_id, payload)


@router.delete(
    "/{technique_id}",
    summary="Удаление техники",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_technique(technique_id: int, technique_service: TechniqueServiceDep):
    """Удаление техники"""
    await technique_service.delete_technique(technique_id)
    return None
