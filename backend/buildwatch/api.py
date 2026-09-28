from fastapi import APIRouter

import buildwatch.infrastructure.settings_views as settings
import buildwatch.infrastructure.views as app
import buildwatch.photos.views as photos
import buildwatch.projects.views as projects
import buildwatch.progress.views as progress
import buildwatch.stages.views as stages
import buildwatch.techniques.views as techniques
import buildwatch.work_types.views as work_types

router = APIRouter()

router.include_router(settings.router)
router.include_router(work_types.router)
router.include_router(projects.router)
router.include_router(progress.router)
router.include_router(stages.router)
router.include_router(photos.router)
router.include_router(techniques.router)
router.include_router(app.router)
