from datetime import datetime, timezone
from typing import Any, Sequence
from buildwatch.infrastructure.database.models.core.techniques import TechniquesORM
from buildwatch.techniques.contracts import TechniqueRepositoryProtocol


class MockTechniqueRepository(TechniqueRepositoryProtocol):
    """Мок-репозиторий техники"""

    def __init__(self) -> None:
        self._data: list[TechniquesORM] = [
            TechniquesORM(
                id=1,
                name="Excavator",
                name_ru="Экскаватор",
                color="#0080FF",
                created_at=datetime.now(timezone.utc),
            ),
            TechniquesORM(
                id=2,
                name="Bulldozer",
                name_ru="Бульдозер",
                color="#B1FF00",
                created_at=datetime.now(timezone.utc),
            ),
            TechniquesORM(
                id=3,
                name="Crane",
                name_ru="Автокран",
                color="#00FFC9",
                created_at=datetime.now(timezone.utc),
            ),
        ]

    async def create_technique(self, name: str, name_ru: str, color: str) -> int:
        new_id = max(t.id for t in self._data) + 1 if self._data else 1
        self._data.append(
            TechniquesORM(
                id=new_id,
                name=name,
                name_ru=name_ru,
                color=color,
                created_at=datetime.now(timezone.utc),
            )
        )
        return new_id

    async def get_techniques(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[TechniquesORM]:
        return self._data

    async def get_technique_by_id(
        self, technique_id: int, *specs: Any
    ) -> TechniquesORM | None:
        return next((t for t in self._data if t.id == technique_id), None)

    async def update_technique(self, technique_id: int, **kwargs: Any) -> None:
        technique = await self.get_technique_by_id(technique_id)
        if technique:
            for k, v in kwargs.items():
                setattr(technique, k, v)

    async def delete_technique(self, technique_id: int) -> None:
        self._data = [t for t in self._data if t.id != technique_id]

    async def get_count(self, model: Any, *specs: Any, **filter_by: Any) -> int:
        return len(self._data)
