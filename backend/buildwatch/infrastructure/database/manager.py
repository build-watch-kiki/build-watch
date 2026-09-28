from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.projects.contracts import ProjectsRepositoryProtocol
from buildwatch.projects.repository import ProjectsRepositoryDep
from buildwatch.stages.contracts import StagesRepositoryProtocol
from buildwatch.stages.repository import StagesRepositoryDep
from buildwatch.work_types.contracts import WorkTypesRepositoryProtocol
from buildwatch.work_types.repository import WorkTypesRepositoryDep


from buildwatch.techniques.contracts import TechniqueRepositoryProtocol
from buildwatch.techniques.repository import TechniquesRepositoryDep
from buildwatch.photos.contracts import PhotosRepositoryProtocol
from buildwatch.photos.repository import PhotosRepositoryDep
from buildwatch.progress.analyzer import DailyProgressAnalyzer
from buildwatch.progress.repository import ProgressRepository, ProgressRepositoryDep
from buildwatch.settings import get_settings


class DBManager:
    """Агрегатор репозиториев и управления транзакцией"""

    def __init__(
        self,
        session: AsyncSession,
        project_repo: ProjectsRepositoryProtocol,
        stage_repo: StagesRepositoryProtocol,
        work_type_repo: WorkTypesRepositoryProtocol,
        technique_repo: TechniqueRepositoryProtocol,
        photos_repo: PhotosRepositoryProtocol,
        progress_repo: ProgressRepository,
    ):
        self._session = session
        self.project_repo = project_repo
        self.stage_repo = stage_repo
        self.work_type_repo = work_type_repo
        self.technique_repo = technique_repo
        self.photos_repo = photos_repo
        self.progress_repo = progress_repo

    async def commit(self) -> None:
        """Фиксация текущей транзакции"""
        await self._session.commit()

    async def rollback(self) -> None:
        """Откат текущей транзакции"""
        await self._session.rollback()

    async def recalculate_progress(self, project_id: int) -> None:
        """Rebuild all materialized analytics after a plan mutation."""

        analyzer = DailyProgressAnalyzer(self.progress_repo, get_settings().analysis)
        dates = await self.progress_repo.list_progress_dates(project_id)
        for analysis_date in dates:
            await analyzer.recalculate(project_id, analysis_date)

    async def list_gantt_progress(self, project_id: int, from_date=None, to_date=None):
        return await self.progress_repo.list_gantt_progress(
            project_id, from_date, to_date
        )


def get_db_manager(
    session: SessionDep,
    project_repo: ProjectsRepositoryDep,
    stage_repo: StagesRepositoryDep,
    work_type_repo: WorkTypesRepositoryDep,
    technique_repo: TechniquesRepositoryDep,
    photos_repo: PhotosRepositoryDep,
    progress_repo: ProgressRepositoryDep,
) -> DBManager:
    """Сборка DBManager из зависимостей"""
    return DBManager(
        session=session,
        project_repo=project_repo,
        stage_repo=stage_repo,
        work_type_repo=work_type_repo,
        technique_repo=technique_repo,
        photos_repo=photos_repo,
        progress_repo=progress_repo,
    )


DBManagerDep = Annotated[DBManager, Depends(get_db_manager)]
