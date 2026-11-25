"""Private object storage backed by Cloudflare R2's S3-compatible API."""

import asyncio
import uuid
from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import get_settings


class ObjectStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.STORAGE_BUCKET
        self.ttl = settings.STORAGE_PRESIGNED_DOWNLOAD_URL_TTL
        endpoint = settings.STORAGE_ENDPOINT_URL
        if not endpoint and settings.STORAGE_ACCOUNT_ID:
            endpoint = f"https://{settings.STORAGE_ACCOUNT_ID}.r2.cloudflarestorage.com"
        if (
            not endpoint
            or not settings.STORAGE_ACCESS_KEY_ID
            or not settings.STORAGE_SECRET_ACCESS_KEY
        ):
            raise RuntimeError("R2 storage is not configured (R2_* or STORAGE_* settings are required)")
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=settings.STORAGE_SECRET_ACCESS_KEY,
            region_name=settings.STORAGE_REGION,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    async def put(self, content: bytes, mime_type: str, prefix: str, extension: str) -> str:
        key = f"{prefix}/{uuid.uuid4().hex}{extension}"
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=mime_type,
        )
        return f"r2://{key}"

    async def presign(self, storage_key: str, download_name: str | None = None) -> str:
        key = storage_key.removeprefix("r2://")
        params = {"Bucket": self.bucket, "Key": key}
        if download_name:
            params["ResponseContentDisposition"] = f'inline; filename="{download_name}"'
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "get_object",
            Params=params,
            ExpiresIn=self.ttl,
        )

    async def presign_put(
        self, key: str, mime_type: str, _size_bytes: int, expires_in: int = 3600
    ) -> str:
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )

    async def create_multipart_upload(self, key: str, mime_type: str) -> str:
        response = await asyncio.to_thread(
            self.client.create_multipart_upload,
            Bucket=self.bucket,
            Key=key,
            ContentType=mime_type,
        )
        upload_id = response.get("UploadId")
        if not upload_id:
            raise RuntimeError("R2 did not return a multipart upload ID.")
        return upload_id

    async def presign_upload_part(
        self, key: str, upload_id: str, part_number: int, expires_in: int = 3600
    ) -> str:
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=expires_in,
        )

    async def complete_multipart_upload(
        self, key: str, upload_id: str, parts: list[dict[str, int | str]]
    ) -> None:
        await asyncio.to_thread(
            self.client.complete_multipart_upload,
            Bucket=self.bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )

    async def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        await asyncio.to_thread(
            self.client.abort_multipart_upload,
            Bucket=self.bucket,
            Key=key,
            UploadId=upload_id,
        )

    async def head(self, key: str) -> dict:
        return await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)

    async def read_prefix(self, key: str, length: int = 32) -> bytes:
        """Read only enough bytes to validate an uploaded object's declared media type."""
        def read() -> bytes:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=key,
                Range=f"bytes=0-{length - 1}",
            )
            body = response["Body"]
            try:
                return body.read(length)
            finally:
                body.close()

        return await asyncio.to_thread(read)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    return ObjectStorage()


def is_r2_key(value: str | None) -> bool:
    return bool(value and value.startswith("r2://"))
