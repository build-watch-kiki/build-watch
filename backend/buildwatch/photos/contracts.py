from datetime import datetime
from typing import Protocol, Sequence


class PhotosRepositoryProtocol(Protocol):
    """Контракт репозитория фотографий"""

    async def create_photo(
        self,
        project_id: int,
        storage_key: str,
        captured_at: datetime | None,
        width: int | None,
        height: int | None,
        format: str | None,
        is_processed: bool = False,
    ) -> int: ...

    async def get_photo_by_id(self, photo_id: int): ...

    async def list_photos(
        self,
        project_id: int,
        limit: int,
        offset: int,
        is_processed: bool | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> Sequence: ...

    async def count_photos(
        self,
        project_id: int,
        is_processed: bool | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> int: ...

    async def create_cv_run(
        self, photo_id: int, width: int | None, height: int | None, format: str | None
    ) -> int: ...

    async def active_annotations(self, photos: Sequence) -> dict[int, tuple]: ...

    async def latest_runs(self, photos: Sequence) -> dict[int, object]: ...

    async def activate_cv_run(self, photo_id: int, cv_run_id: int) -> None: ...

    async def set_processed(self, photo_id: int, is_processed: bool) -> bool: ...
