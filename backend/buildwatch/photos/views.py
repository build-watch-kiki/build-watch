from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi import status

from buildwatch.photos.schemas import PhotoResponse, PhotoUploadResponse
from buildwatch.photos.service import PhotosServiceDep
from buildwatch.progress.schemas import ProgressRangeDep
from buildwatch.shared import BaseDetailSchema, PaginationDep
from buildwatch.shared.schemas import MetadataResponse

router = APIRouter(prefix="/projects/{project_id}/photos", tags=["Снимки"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Загрузка фотографии с камеры",
    response_model=PhotoUploadResponse,
)
async def load_photos(
    photo_service: PhotosServiceDep,
    project_id: int,
    file: UploadFile = File(...),
    captured_at: Annotated[datetime | None, Form(alias="capturedAt")] = None,
):
    photo_id = await photo_service.upload_photo(
        file=file, project_id=project_id, captured_at=captured_at
    )
    return PhotoUploadResponse(id=photo_id)


@router.get(
    "",
    summary="Получение фотографий с камеры для проекта",
    response_model=BaseDetailSchema[PhotoResponse],
)
async def get_project_photos(
    photo_service: PhotosServiceDep,
    project_id: int,
    pagination: PaginationDep,
    date_range: ProgressRangeDep,
    is_processed: bool | None = Query(default=None, alias="isProcessed"),
):
    items, total = await photo_service.list_photos(
        project_id=project_id,
        pagination=pagination,
        is_processed=is_processed,
        from_date=date_range.from_date,
        to_date=date_range.to_date,
    )
    return BaseDetailSchema[PhotoResponse](
        items=items,
        metadata=MetadataResponse(
            total=total, page=pagination.page, page_size=pagination.page_size
        ),
    )


@router.get(
    "/{photo_id}",
    summary="Получение фотографии проекта по ID",
    response_model=PhotoResponse,
)
async def get_project_photo(
    photo_service: PhotosServiceDep,
    project_id: int,
    photo_id: int,
):
    return await photo_service.get_photo(project_id=project_id, photo_id=photo_id)
