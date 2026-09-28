import io
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from types import SimpleNamespace

from PIL import Image
import pytest

from buildwatch.photos.service import BUCKET, MAX_PHOTO_SIZE


def jpeg_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 3)).save(output, format="JPEG")
    return output.getvalue()


async def test_get_project_photos(client, mock_db_manager, mock_s3_client):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.photos_repo.count_photos = AsyncMock(return_value=21)
    mock_db_manager.photos_repo.list_photos = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=7,
                project_id=1,
                storage_key="projects/1/photos/test.jpg",
                captured_at=datetime(2026, 9, 20, tzinfo=timezone.utc),
                created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
                width=1920,
                height=1080,
                format="JPEG",
                is_processed=False,
                active_cv_run_id=None,
            )
        ]
    )
    mock_s3_client.get_presigned_url.return_value = "https://s3/photo?signature=1"
    mock_db_manager.photos_repo.active_annotations = AsyncMock(return_value={})
    mock_db_manager.photos_repo.latest_runs = AsyncMock(
        return_value={7: SimpleNamespace(status="pending")}
    )

    response = await client.get("/projects/1/photos?page=2&pageSize=10")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"] == {
        "page": 2,
        "pageSize": 10,
        "total": 21,
        "totalPages": 3,
    }
    assert data["items"] == [
        {
            "id": 7,
            "name": "test.jpg",
            "url": "https://s3/photo?signature=1",
            "detections": [],
            "capturedAt": "2026-09-20T00:00:00Z",
            "createdAt": "2026-09-21T00:00:00Z",
            "width": 1920,
            "height": 1080,
            "format": "JPEG",
            "isProcessed": False,
            "processingStatus": "pending",
            "model": None,
        }
    ]
    mock_db_manager.photos_repo.list_photos.assert_awaited_once_with(
        project_id=1, limit=10, offset=10, is_processed=None
    )
    mock_db_manager.photos_repo.count_photos.assert_awaited_once_with(
        1, is_processed=None
    )
    mock_s3_client.get_presigned_url.assert_called_once_with(
        BUCKET, "projects/1/photos/test.jpg"
    )


async def test_get_project_photos_project_not_found(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(return_value=None)
    response = await client.get("/projects/999/photos")
    assert response.status_code == 404
    mock_db_manager.photos_repo.list_photos.assert_not_awaited()


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False)])
async def test_get_project_photos_filters_processing_status(
    client, mock_db_manager, value, expected
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    mock_db_manager.photos_repo.count_photos.return_value = 0
    mock_db_manager.photos_repo.list_photos.return_value = []

    response = await client.get(f"/projects/1/photos?isProcessed={value}")

    assert response.status_code == 200
    assert response.json()["metadata"]["total"] == 0
    mock_db_manager.photos_repo.count_photos.assert_awaited_once_with(
        1, is_processed=expected
    )
    mock_db_manager.photos_repo.list_photos.assert_awaited_once_with(
        project_id=1, limit=20, offset=0, is_processed=expected
    )


async def test_get_project_photos_filters_by_local_calendar_date(
    client, mock_db_manager
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    mock_db_manager.photos_repo.count_photos.return_value = 0
    mock_db_manager.photos_repo.list_photos.return_value = []

    response = await client.get("/projects/1/photos?from=2026-09-20&to=2026-09-20")

    assert response.status_code == 200
    count_kwargs = mock_db_manager.photos_repo.count_photos.await_args.kwargs
    list_kwargs = mock_db_manager.photos_repo.list_photos.await_args.kwargs
    assert count_kwargs["from_dt"] == datetime(2026, 9, 19, 21, tzinfo=timezone.utc)
    assert count_kwargs["to_dt"] == datetime(2026, 9, 20, 21, tzinfo=timezone.utc)
    assert list_kwargs["from_dt"] == count_kwargs["from_dt"]
    assert list_kwargs["to_dt"] == count_kwargs["to_dt"]


async def test_get_project_photos_active_cv_run(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    mock_db_manager.photos_repo.count_photos.return_value = 1
    photo = SimpleNamespace(
        id=7,
        project_id=1,
        storage_key="original.jpg",
        active_cv_run_id=34,
        is_processed=True,
        captured_at=None,
        created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
        width=200,
        height=100,
        format="JPEG",
    )
    detection = SimpleNamespace(
        object_id=1,
        class_id=2,
        class_name="crane_truck",
        detection_confidence=0.9,
        activity_confidence=0.8,
        activity_state="active",
        x_center=100,
        y_center=50,
        w=40,
        h=20,
    )
    mock_db_manager.technique_repo.get_techniques.return_value = [
        SimpleNamespace(id=3, name="crane", name_ru="Автокран", color="#00FFC9")
    ]
    mock_db_manager.photos_repo.list_photos.return_value = [photo]
    mock_db_manager.photos_repo.active_annotations.return_value = {
        34: (
            SimpleNamespace(
                image_width=200,
                image_height=100,
                model_name="constr_yolo",
                model_version="v2",
                model_storage_weights="s3://buildwatch-cv/models/v2/best.pt",
            ),
            [detection],
        )
    }
    mock_db_manager.photos_repo.latest_runs.return_value = {
        7: SimpleNamespace(status="succeeded")
    }
    mock_s3_client.get_presigned_url.side_effect = lambda _, key: f"https://s3/{key}"
    response = await client.get("/projects/1/photos")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["url"] == "https://s3/original.jpg"
    assert item["processingStatus"] == "succeeded"
    assert "originalUrl" not in item
    assert item["model"] == {
        "name": "constr_yolo",
        "version": "v2",
        "weights": "s3://buildwatch-cv/models/v2/best.pt",
    }
    assert "previewUrl" not in item
    mock_s3_client.get_presigned_url.assert_called_once_with(BUCKET, "original.jpg")
    assert item["detections"] == [
        {
            "objectId": 1,
            "classId": 2,
            "className": "crane_truck",
            "color": "#00FFC9",
            "technique": {
                "id": 3,
                "name": "crane",
                "nameRu": "Автокран",
                "color": "#00FFC9",
            },
            "confidence": {
                "detection": 0.9,
                "activity": 0.8,
                "activityState": "active",
            },
            "bbox": {
                "format": "xywh_center",
                "xCenterNorm": 0.5,
                "yCenterNorm": 0.5,
                "wNorm": 0.2,
                "hNorm": 0.2,
            },
        }
    ]


async def test_get_project_photo_by_id(client, mock_db_manager, mock_s3_client):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    photo = SimpleNamespace(
        id=7,
        project_id=1,
        storage_key="projects/1/photos/abc/site.webp",
        active_cv_run_id=None,
        is_processed=False,
        captured_at=None,
        created_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        width=800,
        height=500,
        format="WEBP",
    )
    mock_db_manager.photos_repo.get_photo_by_id.return_value = photo
    mock_db_manager.photos_repo.active_annotations.return_value = {}
    mock_db_manager.photos_repo.latest_runs.return_value = {
        7: SimpleNamespace(status="failed")
    }
    mock_s3_client.get_presigned_url.return_value = "https://s3/site.webp"

    response = await client.get("/projects/1/photos/7")

    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["processingStatus"] == "failed"
    mock_db_manager.photos_repo.latest_runs.assert_awaited_once_with([photo])


async def test_get_project_photo_rejects_photo_from_another_project(
    client, mock_db_manager
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    mock_db_manager.photos_repo.get_photo_by_id.return_value = SimpleNamespace(
        id=7, project_id=2
    )

    response = await client.get("/projects/1/photos/7")

    assert response.status_code == 404
    mock_db_manager.photos_repo.active_annotations.assert_not_awaited()


async def test_upload_photo(client, mock_db_manager, mock_s3_client):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_s3_client.put_object = MagicMock(return_value="projects/1/photos/test.webp")
    mock_s3_client.get_presigned_url = MagicMock(return_value="http://minio/test.webp")
    mock_db_manager.photos_repo.create_photo.return_value = 12
    mock_db_manager.photos_repo.create_cv_run.return_value = 34

    with patch("buildwatch.photos.service.broker") as mock_broker:
        mock_broker.publish = AsyncMock()
        response = await client.post(
            "/projects/1/photos",
            files={"file": ("test.jpg", jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 202
        assert response.json() == {"id": 12}
        mock_db_manager.photos_repo.create_photo.assert_awaited_once()
        expected_key = mock_s3_client.put_object.call_args.kwargs["object_name"]
        assert expected_key.startswith("projects/1/photos/")
        assert expected_key.endswith("/test.webp")
        assert len(expected_key.split("/")[-2]) == 32
        assert (
            mock_s3_client.put_object.call_args.kwargs["content_type"] == "image/webp"
        )
        with Image.open(
            io.BytesIO(mock_s3_client.put_object.call_args.kwargs["data"])
        ) as stored_image:
            assert stored_image.format == "WEBP"
            assert stored_image.size == (2, 3)
        assert (
            mock_db_manager.photos_repo.create_photo.await_args.kwargs["storage_key"]
            == expected_key
        )
        mock_db_manager.commit.assert_awaited_once()
        mock_db_manager.photos_repo.create_cv_run.assert_awaited_once_with(
            12, 2, 3, "WEBP"
        )
        assert mock_broker.publish.await_args.kwargs["message"]["cv_run_id"] == 34
        assert (
            mock_broker.publish.await_args.kwargs["message"]["object_path"]
            == expected_key
        )
        assert (
            mock_broker.publish.await_args.kwargs["message"]["content_type"]
            == "image/webp"
        )
        assert mock_broker.publish.await_args.kwargs["message"]["format"] == "WEBP"
        assert mock_broker.publish.await_args.kwargs["mandatory"] is True
        assert mock_broker.publish.await_args.kwargs["persist"] is True


async def test_upload_photo_fails_when_event_cannot_be_routed(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_s3_client.get_presigned_url.return_value = "http://minio/test.jpg"

    with patch("buildwatch.photos.service.broker") as mock_broker:
        mock_broker.publish = AsyncMock(side_effect=RuntimeError("unroutable"))
        response = await client.post(
            "/projects/1/photos",
            files={"file": ("test.jpg", jpeg_bytes(), "image/jpeg")},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Не удалось доставить событие об обработке фотографии"
    }
    mock_db_manager.photos_repo.create_photo.assert_awaited_once()
    mock_db_manager.commit.assert_awaited_once()


async def test_upload_photo_rejects_non_image(client, mock_db_manager, mock_s3_client):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    response = await client.post(
        "/projects/1/photos",
        files={"file": ("test.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 415
    mock_s3_client.put_object.assert_not_called()
    mock_db_manager.photos_repo.create_photo.assert_not_awaited()


async def test_upload_photo_rejects_wrong_content_type(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    response = await client.post(
        "/projects/1/photos",
        files={"file": ("test.jpg", jpeg_bytes(), "text/plain")},
    )
    assert response.status_code == 415
    mock_s3_client.put_object.assert_not_called()


async def test_upload_photo_rejects_mismatched_content_type(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    response = await client.post(
        "/projects/1/photos",
        files={"file": ("test.png", jpeg_bytes(), "image/png")},
    )
    assert response.status_code == 415
    mock_s3_client.put_object.assert_not_called()


async def test_upload_photo_rejects_oversized_file(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    response = await client.post(
        "/projects/1/photos",
        files={"file": ("test.jpg", b"x" * (MAX_PHOTO_SIZE + 1), "image/jpeg")},
    )
    assert response.status_code == 413
    mock_s3_client.put_object.assert_not_called()
    mock_db_manager.photos_repo.create_photo.assert_not_awaited()


async def test_upload_photo_rejects_excessive_resolution(
    client, mock_db_manager, mock_s3_client
):
    mock_db_manager.project_repo.get_project_by_id.return_value = MagicMock(id=1)
    output = io.BytesIO()
    Image.new("1", (6500, 6500)).save(output, format="PNG")
    response = await client.post(
        "/projects/1/photos",
        files={"file": ("test.png", output.getvalue(), "image/png")},
    )
    assert response.status_code == 413
    mock_s3_client.put_object.assert_not_called()
