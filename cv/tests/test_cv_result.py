import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from buildwatchcv.main import warmup_model
from buildwatchcv.infrastructure.broker import CV_RESULT_QUEUE, handle_photo_uploaded
from buildwatchcv.messages import PhotoUploadedMessage
from buildwatchcv.services.mapper import build_response
from buildwatchcv.services.model import _ensure_weights, predict, warmup
from buildwatchcv.services.photo_loader import load_photo
from buildwatchcv.settings import OutputSettings, S3Settings


def uploaded_message() -> PhotoUploadedMessage:
    return PhotoUploadedMessage(
        cv_run_id=9,
        project_id=1,
        filename="photo.jpg",
        object_path="projects/1/photos/photo.jpg",
        url="https://example.com/photo.jpg",
        size=10,
        uploaded_at=datetime.now(timezone.utc),
    )


class CVResultTests(unittest.IsolatedAsyncioTestCase):
    async def test_photo_and_model_use_separate_buckets(self) -> None:
        settings = SimpleNamespace(s3=S3Settings())
        s3 = Mock()
        s3.get_object.return_value = b"photo"
        s3.weights_key.return_value = "models/v1/best.pt"

        with (
            patch("buildwatchcv.services.photo_loader.get_settings", return_value=settings),
            patch("buildwatchcv.services.photo_loader.get_s3_client", return_value=s3),
            patch("buildwatchcv.services.photo_loader._detect_image_info", return_value=(100, 50, "JPEG")),
        ):
            await load_photo("projects/1/photos/photo.jpg")

        s3.get_object.assert_called_once_with("buildwatch", "projects/1/photos/photo.jpg")

        with (
            patch("buildwatchcv.services.model.get_settings", return_value=settings),
            patch("buildwatchcv.services.model.get_s3_client", return_value=s3),
            patch("pathlib.Path.exists", return_value=False),
        ):
            await _ensure_weights("v1")

        s3.download_to_file.assert_called_once_with(
            "buildwatch-cv", "models/v1/best.pt", Path("/tmp/models/v1/best.pt")
        )

    async def test_startup_warms_configured_model(self) -> None:
        settings = SimpleNamespace(s3=SimpleNamespace(model_version=" v2/ "))
        with (
            patch("buildwatchcv.services.model.get_settings", return_value=settings),
            patch(
                "buildwatchcv.services.model._ensure_weights",
                new_callable=AsyncMock,
                return_value=Path("/tmp/models/v2/best.pt"),
            ) as ensure_weights,
            patch("buildwatchcv.services.model._load_yolo_cached") as load_model,
        ):
            await warmup_model()

        ensure_weights.assert_awaited_once_with("v2")
        load_model.assert_called_once_with("/tmp/models/v2/best.pt")

    async def test_warmup_failure_does_not_stop_startup(self) -> None:
        with (
            patch(
                "buildwatchcv.services.model._ensure_weights",
                new_callable=AsyncMock,
                side_effect=RuntimeError("weights unavailable"),
            ),
            patch("buildwatchcv.services.model._load_yolo_cached") as load_model,
            self.assertLogs("buildwatchcv.services.model", level="WARNING") as logs,
        ):
            await warmup()

        load_model.assert_not_called()
        self.assertIn("model warmup failed", logs.output[0])

    async def test_missing_weights_publishes_failed_result(self) -> None:
        message = uploaded_message()
        with (
            patch(
                "buildwatchcv.services.pipeline.run_pipeline",
                new_callable=AsyncMock,
                side_effect=RuntimeError("weights unavailable"),
            ),
            patch(
                "buildwatchcv.infrastructure.broker.broker.publish",
                new_callable=AsyncMock,
            ) as publish,
        ):
            await handle_photo_uploaded(message)

        publish.assert_awaited_once()
        payload = publish.await_args.args[0]
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["cv_run_id"], 9)
        self.assertIn("weights unavailable", payload["error"])
        self.assertEqual(publish.await_args.kwargs["queue"], CV_RESULT_QUEUE)
        self.assertIs(publish.await_args.kwargs["mandatory"], True)
        self.assertIs(publish.await_args.kwargs["persist"], True)

    async def test_publish_error_retries_instead_of_reporting_inference_failure(self) -> None:
        message = uploaded_message()
        response = build_response(message, 100, 50, "JPEG", [], 12)
        with (
            patch(
                "buildwatchcv.services.pipeline.run_pipeline",
                new_callable=AsyncMock,
                return_value=response,
            ),
            patch(
                "buildwatchcv.infrastructure.broker.broker.publish",
                new_callable=AsyncMock,
                side_effect=RuntimeError("broker unavailable"),
            ) as publish,
        ):
            with self.assertRaisesRegex(RuntimeError, "broker unavailable"):
                await handle_photo_uploaded(message)

        publish.assert_awaited_once()
        self.assertEqual(publish.await_args.args[0]["status"], "succeeded")
        self.assertIs(publish.await_args.kwargs["mandatory"], True)
        self.assertIs(publish.await_args.kwargs["persist"], True)

    async def test_predict_propagates_weight_error(self) -> None:
        with patch(
            "buildwatchcv.services.model._ensure_weights",
            new_callable=AsyncMock,
            side_effect=RuntimeError("weights unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "weights unavailable"):
                await predict(b"photo")

    def test_empty_detections_and_configured_weights_prefix(self) -> None:
        message = uploaded_message()
        settings = SimpleNamespace(
            s3=SimpleNamespace(
                bucket="photos", cv_bucket="model-weights", model_version="v1", model_name="detector",
                models_prefix="custom/models",
            )
        )
        with patch("buildwatchcv.services.mapper.get_settings", return_value=settings):
            response = build_response(message, 100, 50, "JPEG", [], 12)

        self.assertEqual(response.detections, [])
        self.assertEqual(
            str(response.processing.model.storage_weights),
            "s3://model-weights/custom/models/v1/best.pt",
        )
        self.assertFalse(OutputSettings().enabled)


if __name__ == "__main__":
    unittest.main()
