import asyncio
from collections.abc import Generator

import boto3
from fastapi import status as http_status
from loguru import logger as log
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import DeleteTypeDef, ObjectIdentifierTypeDef

from wwricu.config import app_config, env
from wwricu.domain.third import AWSConst, AWSS3ListResponse, AWSS3Object, AWSS3Response, AWSResponseBase


class AWSS3Storage:
    bucket: str
    s3_client: S3Client

    def __init__(self, s3_client: S3Client, bucket: str):
        self.bucket = bucket
        self.s3_client = s3_client

    def sync_get(self, key: str) -> bytes:
        # If S3 object_name was not specified, use file_name
        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        s3_resp = AWSS3Response.model_validate(response)
        s3_resp.check()
        return s3_resp.Body.read()

    def sync_put(self, key: str, data: bytes) -> str:
        response = self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=data)
        AWSResponseBase.model_validate(response).check()
        return f'https://{env.RESOURCE_HOSTNAME}/image/{key}'

    def sync_delete(self, key: str):
        response = self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        AWSResponseBase.model_validate(response).check()

    def sync_batch_delete(self, keys: list[str]):
        if not keys:
            return
        response = self.s3_client.delete_objects(
            Bucket=self.bucket,
            Delete=DeleteTypeDef(Objects=[ObjectIdentifierTypeDef(Key=key) for key in keys])
        )
        AWSResponseBase.model_validate(response).check()

    def sync_list_all(self) -> list[AWSS3Object]:
        response = self.s3_client.list_objects_v2(Bucket=self.bucket)
        s3_resp = AWSS3ListResponse.model_validate(response)
        s3_resp.check()
        return s3_resp.Contents

    def sync_list_page(self, page_size: int = 100) -> Generator[AWSS3Object, None, None]:
        continuation_token = None
        while True:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                MaxKeys=page_size,
                ContinuationToken=continuation_token
            ) if continuation_token else self.s3_client.list_objects_v2(Bucket=self.bucket, MaxKeys=page_size)

            s3_resp = AWSS3ListResponse.model_validate(response)
            if s3_resp.ResponseMetadata.HTTPStatusCode != http_status.HTTP_200_OK:
                log.warning(f'Failed to list objects: {s3_resp.ResponseMetadata}')
                break

            yield from s3_resp.Contents
            if not s3_resp.IsTruncated:
                break
            continuation_token = s3_resp.NextContinuationToken

    def generate_presigned_url(self, key: str, expires: int) -> str:
        return self.s3_client.generate_presigned_url(
            AWSConst.GET_OBJECT,
            Params=dict(Bucket=self.bucket, Key=key),
            ExpiresIn=expires
        )

    def get_key_from_url(self, url: str) -> str | None:
        bucket = f'/{self.bucket}/'
        if not url or bucket not in url:
            return None
        url = url.strip()
        return url[url.find(bucket) + len(bucket):]

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self.sync_get, key)

    async def put(self, key: str, data: bytes) -> str:
        return await asyncio.to_thread(self.sync_put, key, data)

    async def delete(self, key: str):
        await asyncio.to_thread(self.sync_delete, key)


aws_s3_client = boto3.client(AWSConst.S3, region_name=AWSConst.REGION)
oss_public = AWSS3Storage(aws_s3_client, app_config.storage.bucket)
oss_private = AWSS3Storage(aws_s3_client, app_config.storage.private_bucket)
