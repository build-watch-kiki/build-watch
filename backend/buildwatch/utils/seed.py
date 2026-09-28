import asyncio
from pathlib import Path

from buildwatch.infrastructure.database.helper import db_helper
from buildwatch.utils.add_project_types import add_project_types
from buildwatch.utils.add_work_types import add_work_types


async def seed():
    """Сидирование справочников из Excel-файла"""

    xlsx = Path("data/Сводный перечень строительных работ_ЛТЦ.xlsx")
    print(f"Загрузка из {xlsx}...")
    async with db_helper.session_maker() as session:
        await add_project_types(xlsx, session)
        await add_work_types(xlsx, session)
        await session.commit()
        print("Готово: сидирование завершено")


if __name__ == "__main__":
    asyncio.run(seed())
