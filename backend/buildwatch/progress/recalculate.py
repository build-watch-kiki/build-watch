"""Idempotent backfill for photos processed before daily analysis was deployed."""

import argparse
import asyncio

from buildwatch.infrastructure.database.helper import db_helper
from buildwatch.progress.analyzer import DailyProgressAnalyzer
from buildwatch.progress.repository import ProgressRepository
from buildwatch.settings import get_settings


async def recalculate(project_id: int | None = None) -> int:
    count = 0
    async with db_helper.session_maker() as session:
        repository = ProgressRepository(session)
        analyzer = DailyProgressAnalyzer(repository, get_settings().analysis)
        photo_times = await repository.list_processed_photo_times()
        days = sorted(
            {
                (photo_project_id, analyzer.analysis_date_for(captured_at))
                for photo_project_id, captured_at in photo_times
                if project_id is None or photo_project_id == project_id
            }
        )
        for photo_project_id, analysis_date in days:
            await analyzer.recalculate(photo_project_id, analysis_date)
            await session.commit()
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int)
    args = parser.parse_args()
    count = asyncio.run(recalculate(args.project_id))
    print(f"Recalculated {count} project days")


if __name__ == "__main__":
    main()
