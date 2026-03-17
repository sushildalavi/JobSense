"""
S3-compatible storage client.

Wraps boto3 to provide async-friendly file operations for uploads,
downloads, deletion, and presigned URL generation.
"""

from __future__ import annotations

import io

import boto3
import structlog
from botocore.exceptions import ClientError

from app.core.config import settings

logger = structlog.get_logger(__name__)


class StorageClient:
    """
    S3 storage client.

    Initialised once and shared application-wide.  All methods are
    synchronous boto3 calls — wrap with asyncio.to_thread() if needed
    in async contexts.
    """

    def __init__(self) -> None:
        self._s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self._bucket = settings.S3_BUCKET_NAME

    # ── Public API ────────────────────────────────────────────────────────────

    def upload_file(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        public: bool = False,
    ) -> str:
        """
        Upload raw bytes to S3 under *key*.

        Args:
            file_bytes: File content.
            key: S3 object key (e.g. ``resumes/user_id/resume.pdf``).
            content_type: MIME type string.
            public: If True, grant public-read ACL.

        Returns:
            Public HTTPS URL or private S3 URI for the uploaded object.
        """
        extra_args: dict = {"ContentType": content_type}
        if public:
            extra_args["ACL"] = "public-read"

        self._s3.upload_fileobj(
            io.BytesIO(file_bytes),
            self._bucket,
            key,
            ExtraArgs=extra_args,
        )
        logger.info("File uploaded to S3", key=key, size_bytes=len(file_bytes))

        if public:
            return f"https://{self._bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        return f"s3://{self._bucket}/{key}"

    def get_file(self, key: str) -> bytes:
        """
        Download an object from S3 and return its raw bytes.

        Raises:
            FileNotFoundError: If the key does not exist.
        """
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"S3 key not found: {key}") from exc
            raise

    def delete_file(self, key: str) -> None:
        """Delete an object from S3. No-op if key does not exist."""
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
            logger.info("File deleted from S3", key=key)
        except ClientError as exc:
            logger.warning("Failed to delete S3 file", key=key, error=str(exc))
            raise

    def generate_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for temporary access to a private S3 object.

        Args:
            key: S3 object key.
            expires: URL lifetime in seconds (default: 1 hour).
            http_method: HTTP method for the presigned URL (``GET`` or ``PUT``).

        Returns:
            HTTPS presigned URL string.
        """
        operation = "get_object" if http_method.upper() == "GET" else "put_object"
        url: str = self._s3.generate_presigned_url(
            operation,
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )
        return url

    def key_exists(self, key: str) -> bool:
        """Return True if the S3 key exists, False otherwise."""
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise


# Singleton — import and use throughout the codebase
storage = StorageClient()
