"""Lazy bounded S3 reads and explicit deployment-only writes."""
from __future__ import annotations

import json
from botocore.config import Config
from botocore.exceptions import ClientError

from src.domain.document_rag import ActivePointer


CLIENT_CONFIG = Config(connect_timeout=3, read_timeout=10, retries={"total_max_attempts": 1})


class DocumentStore:
    def __init__(self, bucket: str, region: str, client=None, session=None):
        self.bucket, self.region, self._client, self._session = bucket, region, client, session

    @property
    def client(self):
        if self._client is None:
            import boto3
            self._client = (self._session or boto3).client("s3", region_name=self.region, config=CLIENT_CONFIG)
        return self._client

    def read_json(self, key: str, *, optional: bool = False):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as error:
            if optional and error.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                return None, None
            raise
        # Every JSON object is bounded. No untrusted large response retained in RAM.
        body = response["Body"]
        try:
            data = body.read(1024 * 1024 + 1)
        finally:
            body.close()
        if len(data) > 1024 * 1024:
            raise ValueError("Stored JSON exceeds 1 MiB")
        return json.loads(data), response["ETag"]

    def active(self, key="rag/active.json"):
        data, etag = self.read_json(key, optional=True)
        return (ActivePointer.model_validate(data) if data else None), etag

    def write_bytes(self, key: str, data: bytes, content_type: str):
        try:
            return self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, IfNoneMatch="*")
        except ClientError as error:
            if error.response["Error"]["Code"] not in {"PreconditionFailed", "ConditionalRequestConflict", "412", "409"}:
                raise
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"]
            try:
                existing = body.read(len(data)+1)
            finally:
                body.close()
            if existing != data:
                raise ValueError("Immutable object already exists with different content") from None

    def write_json(self, key: str, data: dict):
        return self.write_bytes(key, json.dumps(data, sort_keys=True, ensure_ascii=False).encode(), "application/json")

    def publish_pointer(self, pointer: ActivePointer, etag: str | None, key="rag/active.json"):
        condition = {"IfMatch": etag} if etag else {"IfNoneMatch": "*"}
        return self.client.put_object(Bucket=self.bucket, Key=key, Body=pointer.model_dump_json().encode(),
                                      ContentType="application/json", **condition)
