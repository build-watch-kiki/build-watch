from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends

from buildwatch.infrastructure.minio_client import S3Client, S3ClientDep
from buildwatch.photos.repository import PhotosRepositoryDep
from buildwatch.photos.schemas import (
    BBoxResponse,
    ConfidenceResponse,
    DetectionResponse,
    DetectionTechniqueResponse,
)
from buildwatch.progress.messages import (
    detail_messages,
    progress_message,
    status_from_timing,
)
from buildwatch.progress.repository import ProgressRepositoryDep
from buildwatch.progress.schemas import (
    DailyProgressDetailResponse,
    DailyProgressSummaryResponse,
    EvidencePhotoResponse,
    ObservationQualityResponse,
    ProgressQualityResponse,
    ProgressRangeRequest,
    ProgressStagesResponse,
    StageMatchResponse,
    TechniquePlanFactResponse,
    TechniquesResponse,
)
from buildwatch.projects.repository import ProjectsRepositoryDep
from buildwatch.settings import get_settings
from buildwatch.shared.exceptions import NotFoundException
from buildwatch.techniques.mapping import TechniqueMatcher
from buildwatch.techniques.colors import generate_color


class ProgressService:
    def __init__(self, repository, project_repository, photos_repository, s3_client):
        self.repository = repository
        self.project_repository = project_repository
        self.photos_repository = photos_repository
        self.s3_client: S3Client = s3_client
        self.settings = get_settings()

    async def _verify_project(self, project_id: int) -> None:
        if await self.project_repository.get_project_by_id(project_id) is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")

    def _today(self):
        return datetime.now(ZoneInfo(self.settings.analysis.timezone)).date()

    async def list_daily_progress(
        self, project_id: int, request: ProgressRangeRequest
    ) -> list[DailyProgressSummaryResponse]:
        await self._verify_project(project_id)
        items = await self.repository.list_progress(
            project_id, request.from_date, request.to_date
        )
        today = self._today()
        return [self._to_summary(item, today) for item in items]

    async def get_daily_progress(
        self, project_id: int, analysis_date
    ) -> DailyProgressDetailResponse:
        await self._verify_project(project_id)
        item = await self.repository.get_progress_day(project_id, analysis_date)
        if item is None:
            raise NotFoundException(
                f"Аналитика проекта {project_id} за {analysis_date} не найдена"
            )

        photos = [link.photo for link in item.evidence]
        annotations = await self.photos_repository.active_annotations(photos)
        matcher = TechniqueMatcher(await self.repository.load_techniques())
        summary = self._to_summary(item, self._today())
        evidence = [
            self._evidence(link, annotations, matcher) for link in item.evidence
        ]
        evidence_ids = [photo.id for photo in evidence]
        reasons = list(item.data_quality_reasons)
        if item.reason and item.reason not in reasons:
            reasons.insert(0, item.reason)
        summary_data = summary.model_dump(exclude={"quality"})

        return DailyProgressDetailResponse(
            **summary_data,
            techniques=TechniquesResponse(
                stage_id=item.actual_stage_id,
                items=[self._technique(row) for row in item.techniques],
            ),
            messages=detail_messages(
                item,
                summary.status,
                item.techniques,
                evidence_ids,
                summary.message,
            ),
            quality=ProgressQualityResponse(
                level=item.data_quality,
                observations=ObservationQualityResponse(
                    total=item.observation_count,
                    usable=item.usable_observation_count,
                ),
                coverage=self._round(item.processing_coverage) or 0.0,
                agreement=self._round(item.agreement_rate) or 0.0,
                reasons=reasons,
            ),
            evidence=evidence,
        )

    def _to_summary(self, item, today) -> DailyProgressSummaryResponse:
        status = status_from_timing(item.timing_status)
        deviation_count = self._technique_deviation_count(item)
        stages = ProgressStagesResponse(
            previous=self._stage(
                item.previous_stage_id,
                item.previous_stage_name,
                item.previous_score,
            ),
            current=self._stage(
                item.actual_stage_id,
                item.actual_stage_name,
                self._current_score(item),
            ),
            next=self._stage(
                item.next_stage_id,
                item.next_stage_name,
                item.next_score,
            ),
        )
        return DailyProgressSummaryResponse(
            date=item.analysis_date,
            is_final=item.analysis_date < today,
            status=status,
            deviation_days=(None if status == "unknown" else item.time_deviation_days),
            technique_deviation_count=deviation_count,
            message=progress_message(
                item,
                status,
                self.settings.analysis.minimum_stage_score,
                deviation_count,
            ),
            stages=stages,
            quality=item.data_quality,
        )

    @staticmethod
    def _technique_deviation_count(item) -> int:
        return sum(row.is_deviation for row in item.techniques)

    @staticmethod
    def _current_score(item) -> float | None:
        if item.actual_stage_id == item.previous_stage_id:
            return ProgressService._round(item.previous_score)
        if item.actual_stage_id == item.next_stage_id:
            return ProgressService._round(item.next_score)
        return None

    @staticmethod
    def _round(value: float | None) -> float | None:
        return round(value, 5) if value is not None else None

    @staticmethod
    def _stage(
        stage_id: int | None, name: str | None, score: float | None
    ) -> StageMatchResponse | None:
        if stage_id is None or name is None:
            return None
        return StageMatchResponse(
            id=stage_id,
            name=name,
            score=ProgressService._round(score),
        )

    @staticmethod
    def _technique(row) -> TechniquePlanFactResponse:
        status = "on_plan" if row.deviation_type == "none" else row.deviation_type
        return TechniquePlanFactResponse(
            id=row.technique_id,
            name=row.technique_name_ru,
            plan=row.planned_quantity,
            fact=row.actual_quantity,
            delta=row.delta,
            status=status,
        )

    def _evidence(
        self, link, annotations: dict, technique_matcher: TechniqueMatcher
    ) -> EvidencePhotoResponse:
        photo = link.photo
        run, detections = annotations.get(photo.active_cv_run_id, (None, []))
        return EvidencePhotoResponse(
            id=photo.id,
            url=self.s3_client.get_presigned_url(
                self.settings.s3.bucket, photo.storage_key
            ),
            captured_at=photo.captured_at or photo.created_at,
            reason_codes=list(link.reason_codes),
            detections=[
                DetectionResponse(
                    object_id=detection.object_id,
                    class_id=detection.class_id,
                    class_name=detection.class_name,
                    color=(
                        matched.color
                        if (matched := technique_matcher.resolve(detection.class_name))
                        is not None
                        else generate_color(detection.class_name)
                    ),
                    technique=(
                        DetectionTechniqueResponse.model_validate(
                            technique_matcher.resolve(detection.class_name),
                            from_attributes=True,
                        )
                        if technique_matcher.resolve(detection.class_name) is not None
                        else None
                    ),
                    confidence=ConfidenceResponse(
                        detection=detection.detection_confidence,
                        activity=detection.activity_confidence,
                        activity_state=detection.activity_state,
                    ),
                    bbox=BBoxResponse(
                        x_center_norm=(
                            detection.x_center / run.image_width
                            if run and run.image_width
                            else None
                        ),
                        y_center_norm=(
                            detection.y_center / run.image_height
                            if run and run.image_height
                            else None
                        ),
                        w_norm=(
                            detection.w / run.image_width
                            if run and run.image_width
                            else None
                        ),
                        h_norm=(
                            detection.h / run.image_height
                            if run and run.image_height
                            else None
                        ),
                    ),
                )
                for detection in detections
            ],
        )


def get_progress_service(
    repository: ProgressRepositoryDep,
    project_repository: ProjectsRepositoryDep,
    photos_repository: PhotosRepositoryDep,
    s3_client: S3ClientDep,
) -> ProgressService:
    return ProgressService(repository, project_repository, photos_repository, s3_client)


ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]
