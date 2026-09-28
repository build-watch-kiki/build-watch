from datetime import datetime, timezone
from typing import Any, Sequence

from buildwatch.infrastructure.database.models import (
    StageTechniquesORM,
    StagesORM,
    WorkTypesORM,
    TechniquesORM,
)
from buildwatch.stages.contracts import StagesRepositoryProtocol


class MockStageRepository(StagesRepositoryProtocol):
    """Мок-репозиторий этапов для тестирования без БД — иерархия по project_id"""

    def __init__(self) -> None:
        self._work_types: list[WorkTypesORM] = [
            WorkTypesORM(
                id=1,
                name="Демонтаж",
                code="DEM",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            WorkTypesORM(
                id=2,
                name="Возведение",
                code="STR",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            WorkTypesORM(
                id=3,
                name="Электромонтаж",
                code="ELM",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            WorkTypesORM(
                id=4,
                name="Отделочные работы",
                code="FIN",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            WorkTypesORM(
                id=5,
                name="Монтаж конструкций",
                code="MON",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        self._work_type_map = {wt.id: wt for wt in self._work_types}

        # Статические ORM-объекты техники
        self._techniques = {
            1: [
                TechniquesORM(
                    id=1,
                    name="excavator",
                    name_ru="Экскаватор",
                    color="#0080FF",
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
                TechniquesORM(
                    id=2,
                    name="bulldozer",
                    name_ru="Бульдозер",
                    color="#B1FF00",
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
            ],
            2: [
                TechniquesORM(
                    id=3,
                    name="crane",
                    name_ru="Автокран",
                    color="#00FFC9",
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                )
            ],
        }

        # плоский список
        self._stages: list[StagesORM] = [
            StagesORM(
                id=1,
                project_id=1,
                parent_id=None,
                work_type_id=1,
                name="Демонтаж",
                start_dt=datetime(2026, 1, 1, tzinfo=timezone.utc),
                end_dt=datetime(2026, 1, 10, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[1],
            ),
            StagesORM(
                id=2,
                project_id=1,
                parent_id=None,
                work_type_id=2,
                name="Возведение каркаса",
                start_dt=datetime(2026, 1, 11, tzinfo=timezone.utc),
                end_dt=datetime(2026, 2, 20, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 11, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[2],
            ),
            StagesORM(
                id=3,
                project_id=1,
                parent_id=None,
                work_type_id=3,
                name="Электромонтаж здания",
                start_dt=datetime(2026, 2, 21, tzinfo=timezone.utc),
                end_dt=datetime(2026, 3, 15, tzinfo=timezone.utc),
                created_at=datetime(2026, 2, 21, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[3],
            ),
            # Подэтапы Демонтажа
            StagesORM(
                id=4,
                project_id=1,
                parent_id=1,
                work_type_id=1,
                name="Демонтаж стен",
                start_dt=datetime(2026, 1, 1, tzinfo=timezone.utc),
                end_dt=datetime(2026, 1, 5, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[1],
            ),
            StagesORM(
                id=5,
                project_id=1,
                parent_id=1,
                work_type_id=1,
                name="Вывоз мусора",
                start_dt=datetime(2026, 1, 6, tzinfo=timezone.utc),
                end_dt=datetime(2026, 1, 10, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[1],
            ),
            # Подэтапы Возведения
            StagesORM(
                id=6,
                project_id=1,
                parent_id=2,
                work_type_id=5,
                name="Монтаж колонн",
                start_dt=datetime(2026, 1, 11, tzinfo=timezone.utc),
                end_dt=datetime(2026, 1, 20, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 11, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[5],
            ),
            StagesORM(
                id=7,
                project_id=1,
                parent_id=2,
                work_type_id=5,
                name="Монтаж балок",
                start_dt=datetime(2026, 1, 21, tzinfo=timezone.utc),
                end_dt=datetime(2026, 2, 10, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 21, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[5],
            ),
            StagesORM(
                id=8,
                project_id=1,
                parent_id=7,
                work_type_id=5,
                name="Сварка узлов",
                start_dt=datetime(2026, 1, 21, tzinfo=timezone.utc),
                end_dt=datetime(2026, 1, 30, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 21, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[5],
            ),
            StagesORM(
                id=9,
                project_id=1,
                parent_id=7,
                work_type_id=2,
                name="Заливка перекрытий",
                start_dt=datetime(2026, 2, 1, tzinfo=timezone.utc),
                end_dt=datetime(2026, 2, 15, tzinfo=timezone.utc),
                created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[2],
            ),
            # Подэтапы Электромонтажа
            StagesORM(
                id=10,
                project_id=1,
                parent_id=3,
                work_type_id=3,
                name="Прокладка кабеля",
                start_dt=datetime(2026, 2, 21, tzinfo=timezone.utc),
                end_dt=datetime(2026, 3, 1, tzinfo=timezone.utc),
                created_at=datetime(2026, 2, 21, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[3],
            ),
            StagesORM(
                id=11,
                project_id=1,
                parent_id=3,
                work_type_id=3,
                name="Установка щитов",
                start_dt=datetime(2026, 3, 2, tzinfo=timezone.utc),
                end_dt=datetime(2026, 3, 10, tzinfo=timezone.utc),
                created_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[3],
            ),
            StagesORM(
                id=12,
                project_id=1,
                parent_id=11,
                work_type_id=3,
                name="Пусконаладка",
                start_dt=datetime(2026, 3, 11, tzinfo=timezone.utc),
                end_dt=datetime(2026, 3, 15, tzinfo=timezone.utc),
                created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[3],
            ),
            # Проект 2
            StagesORM(
                id=13,
                project_id=2,
                parent_id=None,
                work_type_id=4,
                name="Отделка фасада",
                start_dt=datetime(2026, 4, 1, tzinfo=timezone.utc),
                end_dt=datetime(2026, 4, 30, tzinfo=timezone.utc),
                created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[4],
            ),
            StagesORM(
                id=14,
                project_id=2,
                parent_id=13,
                work_type_id=4,
                name="Покраска",
                start_dt=datetime(2026, 4, 1, tzinfo=timezone.utc),
                end_dt=datetime(2026, 4, 15, tzinfo=timezone.utc),
                created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
                children=[],
                work_type=self._work_type_map[4],
            ),
        ]

        # Связи техники хранят количество так же, как SQL-репозиторий.
        for stage in self._stages:
            stage.technique_links = [
                StageTechniquesORM(technique=technique, quantity=1)
                for technique in self._techniques.get(stage.project_id, [])
            ]

        # Связываем children
        by_id = {s.id: s for s in self._stages}
        for stage in self._stages:
            if stage.parent_id is not None and stage.parent_id in by_id:
                parent = by_id[stage.parent_id]
                if stage not in parent.children:
                    parent.children.append(stage)

    async def create_stage(
        self, project_id, parent_id, work_type_id, name, start_dt, end_dt
    ) -> int:
        new_id = max(s.id for s in self._stages) + 1 if self._stages else 1
        stage = StagesORM(
            id=new_id,
            project_id=project_id,
            parent_id=parent_id,
            work_type_id=work_type_id,
            name=name,
            start_dt=start_dt,
            end_dt=end_dt,
            created_at=datetime.now(timezone.utc),
            children=[],
            work_type=self._work_type_map.get(work_type_id),
            technique_links=[],
        )
        self._stages.append(stage)
        if parent_id is not None:
            for parent in self._stages:
                if parent.id == parent_id:
                    parent.children.append(stage)
                    break
        return new_id

    async def get_stages(self, *specs: Any, **filter_by: Any) -> Sequence[StagesORM]:
        stages = self._stages
        if "project_id" in filter_by:
            stages = [s for s in stages if s.project_id == filter_by["project_id"]]
        return stages

    async def get_count(self, model: Any, *specs: Any, **filter_by: Any) -> int:
        stages = self._stages
        if "project_id" in filter_by:
            stages = [s for s in stages if s.project_id == filter_by["project_id"]]
        return len(stages)

    async def get_stage_by_id(self, stage_id: int, *specs: Any) -> StagesORM | None:
        return next((s for s in self._stages if s.id == stage_id), None)

    async def update_stage(self, stage_id: int, **kwargs: Any) -> None:
        stage = await self.get_stage_by_id(stage_id)
        if stage:
            for k, v in kwargs.items():
                setattr(stage, k, v)
            if "work_type_id" in kwargs:
                stage.work_type = self._work_type_map.get(kwargs["work_type_id"])

    async def delete_stage(self, stage_id: int) -> None:
        self._stages = [s for s in self._stages if s.id != stage_id]
        for s in self._stages:
            s.children = [c for c in s.children if c.id != stage_id]

    async def set_stage_techniques(
        self, stage_id: int, techniques: list[tuple[int, int]]
    ) -> None:
        stage = await self.get_stage_by_id(stage_id)
        if stage is None:
            return
        by_id = {
            technique.id: technique
            for group in self._techniques.values()
            for technique in group
        }
        stage.technique_links = [
            StageTechniquesORM(technique=by_id[technique_id], quantity=quantity)
            for technique_id, quantity in techniques
        ]
