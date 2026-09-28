import io
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from datetime import timezone
from typing import Annotated, Tuple
from uuid import uuid4
from zoneinfo import ZoneInfo

from PIL import Image, ExifTags, UnidentifiedImageError
from fastapi import Depends, UploadFile
from fastapi import status

from buildwatch.infrastructure.broker import NEW_PHOTO_QUEUE, broker
from buildwatch.infrastructure.database.manager import DBManager, DBManagerDep
from buildwatch.infrastructure.minio_client import S3Client, S3ClientDep
from buildwatch.photos.schemas import (
    BBoxResponse,
    ConfidenceResponse,
    DetectionTechniqueResponse,
    DetectionResponse,
    PhotoModelResponse,
    PhotoResponse,
    PhotoUploadedMessage,
)
from buildwatch.settings import get_settings
from buildwatch.shared.exceptions import BuildWatchException, NotFoundException
from buildwatch.shared.schemas import PaginationSchema
from buildwatch.techniques.colors import generate_color
from buildwatch.techniques.mapping import TechniqueMatcher

settings = get_settings()
logger = logging.getLogger(__name__)
BUCKET = settings.s3.bucket
MAX_PHOTO_SIZE = 20 * 1024 * 1024
MAX_PHOTO_PIXELS = 40_000_000
IMAGE_CONTENT_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png"}
STORAGE_IMAGE_FORMAT = "WEBP"
STORAGE_IMAGE_CONTENT_TYPE = "image/webp"
WEBP_QUALITY = 90
WEBP_METHOD = 6
# Допуск на рассинхрон часов клиента/сервера при проверке "даты из будущего".
FUTURE_SKEW = timedelta(minutes=5)


def normalize_captured_at(value: datetime | date) -> datetime:
    """Привести ручную дату к aware datetime в UTC.

    date -> midnight UTC, naive datetime -> UTC, aware -> astimezone(UTC).
    """
    if isinstance(value, datetime):
        normalized = value
    else:
        normalized = datetime.combine(value, time.min)
    if normalized.tzinfo is None:
        return normalized.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class PhotoMetadata:
    filename: str
    file_size: int
    width: int | None
    height: int | None
    format: str | None
    created_at: datetime | None


class PhotosService:
    PHOTOS_PATH = "photos"

    def __init__(self, s3_client: S3Client, db_manager: DBManager):
        self.s3_client = s3_client
        self.db_manager = db_manager

    def new_photo_in_project(self, project_id: int, file_name: str) -> str:
        safe_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
        return f"projects/{project_id}/{self.PHOTOS_PATH}/{uuid4().hex}/{safe_name}"

    async def _verify_project_exists(self, project_id: int):
        project = await self.db_manager.project_repo.get_project_by_id(
            project_id=project_id
        )
        if not project:
            raise NotFoundException(f"Проект с id {project_id} не найден")

    def _extract_image_metadata(
        self, content: bytes, file_name_hint: str | None
    ) -> PhotoMetadata:
        file_size = len(content)
        filename = file_name_hint or datetime.now().strftime("%Y%m%d%H%M%S")

        width, height, img_format, created_at = None, None, None, None
        try:
            with Image.open(io.BytesIO(content)) as img:
                width, height = img.size
                img_format = img.format
                if img_format not in IMAGE_CONTENT_TYPES:
                    raise BuildWatchException(
                        detail="Допустимы только изображения JPEG и PNG",
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )
                if width * height > MAX_PHOTO_PIXELS:
                    raise BuildWatchException(
                        detail="Разрешение фотографии превышает 40 мегапикселей",
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    )
                img.verify()

            with Image.open(io.BytesIO(content)) as img:
                img.load()

                exif_data = img.getexif()
                if exif_data:
                    for tag_id, val in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag in ("DateTimeOriginal", "DateTime"):
                            try:
                                created_at = datetime.strptime(
                                    val, "%Y:%m:%d %H:%M:%S"
                                ).replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                pass
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError,
        ) as exc:
            raise BuildWatchException(
                detail="Файл не является корректным изображением JPEG или PNG",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            ) from exc

        if not created_at:
            created_at = datetime.now(timezone.utc)

        return PhotoMetadata(
            file_size=file_size,
            filename=filename,
            width=width,
            height=height,
            format=img_format,
            created_at=created_at,
        )

    @staticmethod
    def _webp_filename(filename: str) -> str:
        safe_name = filename.replace("\\", "/").rsplit("/", 1)[-1]
        stem = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name
        return f"{stem}.webp"

    def _convert_to_webp(
        self, content: bytes, metadata: PhotoMetadata
    ) -> tuple[bytes, PhotoMetadata]:
        """Сохраняет единственную оптимизированную версию фотографии в WebP."""

        with Image.open(io.BytesIO(content)) as img:
            has_alpha = img.mode in {"RGBA", "LA"} or "transparency" in img.info
            converted = img.convert("RGBA" if has_alpha else "RGB")
            output = io.BytesIO()
            converted.save(
                output,
                format=STORAGE_IMAGE_FORMAT,
                quality=WEBP_QUALITY,
                method=WEBP_METHOD,
            )

        webp_content = output.getvalue()
        return webp_content, PhotoMetadata(
            filename=self._webp_filename(metadata.filename),
            file_size=len(webp_content),
            width=metadata.width,
            height=metadata.height,
            format=STORAGE_IMAGE_FORMAT,
            created_at=metadata.created_at,
        )

    def _save_to_s3(
        self,
        project_id: int,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str]:
        object_path = self.new_photo_in_project(
            project_id=project_id, file_name=filename
        )
        self.s3_client.put_object(
            bucket=BUCKET,
            object_name=object_path,
            data=content,
            content_type=content_type,
        )
        presigned_url = self.s3_client.get_presigned_url(BUCKET, object_path)
        return object_path, presigned_url

    @staticmethod
    async def _publish_photo_event(message_data: PhotoUploadedMessage) -> None:
        try:
            await broker.publish(
                message=message_data.model_dump(mode="json"),
                queue=NEW_PHOTO_QUEUE,
                mandatory=True,
                persist=True,
            )
        except Exception as exc:
            logger.exception(
                "Не удалось доставить событие о фото %s проекта %d",
                message_data.filename,
                message_data.project_id,
            )
            raise BuildWatchException(
                detail="Не удалось доставить событие об обработке фотографии",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        logger.info(
            "Событие о новой фотографии (проект %d, файл %s) доставлено в очередь",
            message_data.project_id,
            message_data.filename,
        )

    async def upload_photo(
        self,
        file: UploadFile,
        project_id: int,
        captured_at: datetime | date | None = None,
    ) -> int:
        await self._verify_project_exists(project_id)

        captured_at_override: datetime | None = None
        if captured_at is not None:
            captured_at_override = normalize_captured_at(captured_at)
            if captured_at_override > datetime.now(timezone.utc) + FUTURE_SKEW:
                raise BuildWatchException(
                    detail="Дата снимка не может быть в будущем",
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                )

        if file.content_type not in IMAGE_CONTENT_TYPES.values():
            raise BuildWatchException(
                detail="Допустимы только изображения JPEG и PNG",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        content = await file.read(MAX_PHOTO_SIZE + 1)
        if len(content) > MAX_PHOTO_SIZE:
            raise BuildWatchException(
                detail="Размер фотографии не должен превышать 20 МиБ",
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            )
        if not content:
            raise BuildWatchException(
                detail="Файл фотографии пуст",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        metadata = self._extract_image_metadata(content, file.filename)
        # Ручная дата важнее EXIF: если передана — перезаписывает метаданные.
        captured_at_final = (
            captured_at_override if captured_at_override is not None else metadata.created_at
        )
        content_type = IMAGE_CONTENT_TYPES[metadata.format]
        if file.content_type != content_type:
            raise BuildWatchException(
                detail="Тип файла не соответствует содержимому изображения",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        content, metadata = self._convert_to_webp(content, metadata)
        content_type = STORAGE_IMAGE_CONTENT_TYPE
        uploaded_at = datetime.now(timezone.utc)

        object_path, presigned_url = self._save_to_s3(
            project_id, metadata.filename, content, content_type
        )

        try:
            photo_id = await self.db_manager.photos_repo.create_photo(
                project_id=project_id,
                storage_key=object_path,
                captured_at=captured_at_final,
                width=metadata.width,
                height=metadata.height,
                format=metadata.format,
            )
            cv_run_id = await self.db_manager.photos_repo.create_cv_run(
                photo_id, metadata.width, metadata.height, metadata.format
            )
            await self.db_manager.commit()
        except Exception:
            await self.db_manager.rollback()
            try:
                self.s3_client.remove_object(BUCKET, object_path)
            except Exception:
                logger.exception(
                    "Не удалось удалить фото %s после ошибки БД", object_path
                )
            raise

        message_data = PhotoUploadedMessage(
            project_id=project_id,
            cv_run_id=cv_run_id,
            filename=metadata.filename,
            object_path=object_path,
            url=presigned_url,
            size=metadata.file_size,
            content_type=content_type,
            width=metadata.width,
            height=metadata.height,
            format=metadata.format,
            created_at=captured_at_final,
            uploaded_at=uploaded_at,
        )
        logger.info(message_data.model_dump())

        await self._publish_photo_event(message_data)
        return photo_id

    async def _save_file_to_s3(
        self, file: UploadFile, project_id: int
    ) -> tuple[str, str]:
        """Сохраняем файл в S3"""

        content = await file.read()
        filename = file.filename or datetime.now().strftime("%Y%m%d%H%M%S")
        object_path, presigned_url = self._save_to_s3(project_id, filename, content)
        return filename, object_path

    async def list_photos(
        self,
        project_id: int,
        pagination: PaginationSchema,
        is_processed: bool | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[PhotoResponse], int]:
        """Страница фотографий проекта из БД с временными ссылками на файлы."""

        await self._verify_project_exists(project_id)
        analysis_timezone = ZoneInfo(settings.analysis.timezone)
        from_dt = (
            datetime.combine(from_date, time.min, tzinfo=analysis_timezone).astimezone(
                timezone.utc
            )
            if from_date
            else None
        )
        to_dt = (
            datetime.combine(
                to_date + timedelta(days=1), time.min, tzinfo=analysis_timezone
            ).astimezone(timezone.utc)
            if to_date
            else None
        )
        date_filters = {}
        if from_dt is not None:
            date_filters["from_dt"] = from_dt
        if to_dt is not None:
            date_filters["to_dt"] = to_dt
        total = await self.db_manager.photos_repo.count_photos(
            project_id, is_processed=is_processed, **date_filters
        )
        photos = await self.db_manager.photos_repo.list_photos(
            project_id=project_id,
            limit=pagination.page_size,
            offset=(pagination.page - 1) * pagination.page_size,
            is_processed=is_processed,
            **date_filters,
        )
        return await self._photo_responses(photos), total

    async def get_photo(self, project_id: int, photo_id: int) -> PhotoResponse:
        """Return one project photo with its current CV annotations."""

        await self._verify_project_exists(project_id)
        photo = await self.db_manager.photos_repo.get_photo_by_id(photo_id)
        if photo is None or photo.project_id != project_id:
            raise NotFoundException(
                f"Фотография с id {photo_id} не найдена в проекте {project_id}"
            )
        return (await self._photo_responses([photo]))[0]

    async def _photo_responses(self, photos) -> list[PhotoResponse]:
        if not photos:
            return []
        annotations = await self.db_manager.photos_repo.active_annotations(photos)
        latest_runs = await self.db_manager.photos_repo.latest_runs(photos)
        techniques = (
            list(await self.db_manager.technique_repo.get_techniques())
            if annotations
            else []
        )
        technique_matcher = TechniqueMatcher(techniques)
        return [
            PhotoResponse(
                id=photo.id,
                project_id=photo.project_id,
                name=photo.storage_key.rsplit("/", 1)[-1],
                url=(
                    original_url := self.s3_client.get_presigned_url(
                        BUCKET, photo.storage_key
                    )
                ),
                original_url=original_url,
                detections=[
                    DetectionResponse(
                        object_id=item.object_id,
                        class_id=item.class_id,
                        class_name=item.class_name,
                        color=(
                            matched.color
                            if (matched := technique_matcher.resolve(item.class_name))
                            is not None
                            else generate_color(item.class_name)
                        ),
                        technique=(
                            DetectionTechniqueResponse.model_validate(
                                matched,
                                from_attributes=True,
                            )
                            if matched is not None
                            else None
                        ),
                        confidence=ConfidenceResponse(
                            detection=item.detection_confidence,
                            activity=item.activity_confidence,
                            activity_state=item.activity_state,
                        ),
                        bbox=BBoxResponse(
                            x_center=item.x_center,
                            y_center=item.y_center,
                            w=item.w,
                            h=item.h,
                            x_center_norm=(
                                item.x_center / run.image_width
                                if run.image_width
                                else None
                            ),
                            y_center_norm=(
                                item.y_center / run.image_height
                                if run.image_height
                                else None
                            ),
                            w_norm=(
                                item.w / run.image_width if run.image_width else None
                            ),
                            h_norm=(
                                item.h / run.image_height if run.image_height else None
                            ),
                        ),
                    )
                    for run, detections in [
                        annotations.get(photo.active_cv_run_id, (None, []))
                    ]
                    if photo.is_processed and run is not None
                    for item in detections
                ],
                captured_at=photo.captured_at,
                created_at=photo.created_at,
                width=photo.width,
                height=photo.height,
                format=photo.format,
                is_processed=photo.is_processed,
                processing_status=(
                    latest_run.status
                    if (latest_run := latest_runs.get(photo.id)) is not None
                    else ("succeeded" if photo.is_processed else "pending")
                ),
                model=(
                    PhotoModelResponse(
                        name=run.model_name,
                        version=run.model_version,
                        weights=run.model_storage_weights,
                    )
                    if (run := annotations.get(photo.active_cv_run_id, (None, []))[0])
                    and getattr(run, "model_name", None)
                    and getattr(run, "model_version", None)
                    and getattr(run, "model_storage_weights", None)
                    else None
                ),
            )
            for photo in photos
        ]


def get_photo_service(s3_client: S3ClientDep, db_manager: DBManagerDep):
    return PhotosService(s3_client=s3_client, db_manager=db_manager)


PhotosServiceDep = Annotated[PhotosService, Depends(get_photo_service)]
