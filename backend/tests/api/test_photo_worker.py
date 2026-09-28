import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from buildwatch.photos.repository import PhotosRepository
from buildwatch.photos.schemas import CVResultMessage
from buildwatch.photos.worker import consume_cv_result, process_cv_result


def result_message(key="original.jpg", status="succeeded", detections=None):
    if detections is None:
        detections = [
            {
                "object_id": 1,
                "class_id": 2,
                "class_name": "crane",
                "confidence": {
                    "detection": 0.9,
                    "activity": 0.8,
                    "activity_state": "active",
                },
                "bbox": {
                    "format": "xywh_center",
                    "x_center": 50,
                    "y_center": 25,
                    "w": 20,
                    "h": 10,
                    "x_center_norm": 0.5,
                },
            }
        ]
    return CVResultMessage.model_validate(
        {
            "cv_run_id": 9,
            "status": status,
            "result": (
                {
                    "image_info": {
                        "key": key,
                        "width": 100,
                        "height": 50,
                        "format": "JPEG",
                    },
                    "processing": {
                        "inference_ms": 15,
                        "model": {
                            "name": "detector",
                            "version": "1",
                            "storage_weights": "s3://weights",
                        },
                    },
                    "detections": detections,
                }
                if status == "succeeded"
                else None
            ),
            "error": "inference failed" if status == "failed" else None,
        }
    )


@pytest.mark.parametrize("status", ["succeeded", "failed"])
async def test_cv_result_persists_once(status):
    run = SimpleNamespace(id=9, photo_id=3, status="pending", completed_at=None)
    repo = AsyncMock()
    repo.lock_cv_run.return_value = run
    repo.get_photo_by_id.return_value = SimpleNamespace(storage_key="original.jpg")

    async def save_success(*_):
        run.status = "succeeded"

    repo.save_cv_success.side_effect = save_success
    commit = AsyncMock()
    first = await process_cv_result(result_message(status=status), repo, commit)
    assert first is (status == "succeeded")
    assert run.status == status
    commit.assert_awaited_once()
    if status == "succeeded":
        repo.save_cv_success.assert_awaited_once()
        repo.activate_cv_run.assert_awaited_once_with(3, 9)
    else:
        repo.save_cv_success.assert_not_awaited()
        repo.activate_cv_run.assert_not_awaited()
    assert await process_cv_result(result_message(status=status), repo, commit) is False
    commit.assert_awaited_once()


@pytest.mark.parametrize("detections", [[], None])
async def test_cv_json_message_saves_and_activates_once(detections):
    payload = result_message(detections=detections).model_dump(mode="json")
    message = CVResultMessage.model_validate_json(json.dumps(payload))
    run = SimpleNamespace(id=9, photo_id=3, status="pending")
    photo = SimpleNamespace(
        id=3,
        project_id=1,
        storage_key="original.jpg",
        captured_at=SimpleNamespace(),
        created_at=SimpleNamespace(),
        active_cv_run_id=None,
        is_processed=False,
    )
    session = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=photo)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    repository = PhotosRepository(session)
    repository.lock_cv_run = AsyncMock(return_value=run)
    repository.get_photo_by_id = AsyncMock(return_value=photo)
    analyzer = MagicMock()
    analyzer.analysis_date_for.return_value = SimpleNamespace()
    analyzer.recalculate_from = AsyncMock()
    with (
        patch("buildwatch.photos.worker.db_helper.session_maker", return_value=context),
        patch("buildwatch.photos.worker.PhotosRepository", return_value=repository),
        patch("buildwatch.photos.worker.DailyProgressAnalyzer", return_value=analyzer),
    ):
        await consume_cv_result(message)
        await consume_cv_result(message)
    assert run.status == "succeeded"
    assert photo.active_cv_run_id == 9
    assert photo.is_processed is True
    assert (run.model_name, run.model_version, run.image_width, run.image_height) == (
        "detector",
        "1",
        100,
        50,
    )
    assert session.add_all.call_count == 1
    stored = list(session.add_all.call_args.args[0])
    assert len(stored) == len(message.result.detections)
    if stored:
        assert (stored[0].x_center, stored[0].y_center, stored[0].w, stored[0].h) == (
            50,
            25,
            20,
            10,
        )
    session.commit.assert_awaited_once()
    analyzer.recalculate_from.assert_awaited_once()


async def test_cv_result_rejects_wrong_image_key():
    repo = AsyncMock()
    repo.lock_cv_run.return_value = SimpleNamespace(id=9, photo_id=3, status="pending")
    repo.get_photo_by_id.return_value = SimpleNamespace(storage_key="original.jpg")
    commit = AsyncMock()
    with pytest.raises(ValueError, match="image key"):
        await process_cv_result(result_message(key="other.jpg"), repo, commit)
    repo.save_cv_success.assert_not_awaited()
    repo.activate_cv_run.assert_not_awaited()
    commit.assert_not_awaited()


async def test_cv_result_stores_metadata_and_pixel_bbox_only():
    session = MagicMock()
    session.flush = AsyncMock()
    repo = PhotosRepository(session)
    run = SimpleNamespace(id=9, status="pending")
    await repo.save_cv_success(run, result_message().result)
    assert (run.status, run.model_name, run.model_version, run.inference_ms) == (
        "succeeded",
        "detector",
        "1",
        15,
    )
    assert (run.image_width, run.image_height, run.image_format) == (100, 50, "JPEG")
    stored = list(session.add_all.call_args.args[0])[0]
    assert (stored.x_center, stored.y_center, stored.w, stored.h) == (50, 25, 20, 10)
    assert "x_center_norm" not in stored.__table__.columns


@pytest.mark.parametrize(
    ("current_run_id", "incoming_run_id", "expected_run_id"),
    [(11, 9, 11), (9, 11, 11), (None, 9, 9)],
)
async def test_only_newest_successful_run_is_active(
    current_run_id, incoming_run_id, expected_run_id
):
    photo = SimpleNamespace(
        active_cv_run_id=current_run_id, is_processed=bool(current_run_id)
    )
    session = MagicMock()
    session.scalar = AsyncMock(return_value=photo)
    session.flush = AsyncMock()
    repo = PhotosRepository(session)
    await repo.activate_cv_run(3, incoming_run_id)
    assert photo.active_cv_run_id == expected_run_id
    assert photo.is_processed is True


async def test_failed_newer_run_keeps_previous_success():
    run = SimpleNamespace(id=11, photo_id=3, status="pending", completed_at=None)
    repo = AsyncMock()
    repo.lock_cv_run.return_value = run
    commit = AsyncMock()
    await process_cv_result(result_message(status="failed"), repo, commit)
    assert run.status == "failed"
    repo.activate_cv_run.assert_not_awaited()


async def test_activation_failure_rolls_back_cv_result():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    repo = AsyncMock()
    repo.lock_cv_run.return_value = SimpleNamespace(id=9, photo_id=3, status="pending")
    repo.get_photo_by_id.return_value = SimpleNamespace(storage_key="original.jpg")
    repo.activate_cv_run.side_effect = RuntimeError("database failure")
    with (
        patch("buildwatch.photos.worker.db_helper.session_maker", return_value=context),
        patch("buildwatch.photos.worker.PhotosRepository", return_value=repo),
    ):
        with pytest.raises(RuntimeError, match="database failure"):
            await consume_cv_result(result_message())
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()
