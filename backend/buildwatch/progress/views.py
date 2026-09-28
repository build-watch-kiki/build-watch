from datetime import date

from fastapi import APIRouter

from buildwatch.progress.schemas import (
    DailyProgressDetailResponse,
    DailyProgressSummaryResponse,
    ProgressRangeDep,
)
from buildwatch.progress.service import ProgressServiceDep
from buildwatch.shared.schemas import BaseDetailSchema, GanttMetadata

router = APIRouter(
    prefix="/projects/{project_id}/progress", tags=["Прогресс и отклонения"]
)


@router.get(
    "/daily",
    summary="Суточная история фактического прогресса и отклонений",
    response_model=BaseDetailSchema[DailyProgressSummaryResponse, GanttMetadata],
)
async def get_daily_progress(
    project_id: int,
    progress_service: ProgressServiceDep,
    request: ProgressRangeDep,
):
    items = await progress_service.list_daily_progress(project_id, request)
    return BaseDetailSchema[DailyProgressSummaryResponse, GanttMetadata](
        items=items, metadata=GanttMetadata(total=len(items))
    )


@router.get(
    "/daily/{analysis_date}",
    summary="Подробный фактический прогресс и отклонения за день",
    response_model=DailyProgressDetailResponse,
)
async def get_daily_progress_detail(
    project_id: int,
    analysis_date: date,
    progress_service: ProgressServiceDep,
):
    return await progress_service.get_daily_progress(project_id, analysis_date)
