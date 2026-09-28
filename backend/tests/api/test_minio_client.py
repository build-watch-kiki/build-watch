from datetime import timedelta
from unittest.mock import MagicMock, patch

from buildwatch.infrastructure.minio_client import (
    BROWSER_CACHE_CONTROL,
    S3Client,
)


@patch("buildwatch.infrastructure.minio_client.Minio")
def test_presigned_url_is_reused_with_browser_cache_headers(mock_minio):
    minio_client = MagicMock()
    minio_client.presigned_get_object.return_value = "https://s3/photo?signature=1"
    mock_minio.return_value = minio_client
    s3_client = S3Client(s3_settings=MagicMock(s3=MagicMock(endpoint="http://minio")))

    first_url = s3_client.get_presigned_url("photos", "projects/1/photo.jpg")
    second_url = s3_client.get_presigned_url("photos", "projects/1/photo.jpg")

    assert first_url == second_url
    minio_client.presigned_get_object.assert_called_once_with(
        "photos",
        "projects/1/photo.jpg",
        expires=timedelta(days=1),
        response_headers={"response-cache-control": BROWSER_CACHE_CONTROL},
    )
