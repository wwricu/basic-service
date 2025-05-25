from typing import Generator

import boto3
from botocore.client import BaseClient
from fastapi import status as http_status
from loguru import logger as log

from wwricu.config import StorageConfig
from wwricu.domain.third import AWSConst, AWSS3ListResponse, AWSS3Object, AWSS3Response, AWSResponseBase


class AWSS3Storage:
    bucket: str
    s3_client: BaseClient

    def __init__(self, s3_client: BaseClient, bucket: str):
        self.bucket = bucket
        self.s3_client = s3_client

    def get(self, key: str) -> bytes:
        # If S3 object_name was not specified, use file_name
        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        response = AWSS3Response.model_validate(response)
        response.check()
        return response.Body.read()

    def put(self, key: str, data: bytes) -> str:
        response = self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=data)
        AWSResponseBase.model_validate(response).check()
        return f'https://{AWSConst.S3}.{StorageConfig.region}.{AWSConst.AWS_DOMAIN}/{self.bucket}/{key}'

    def delete(self, key: str):
        response = self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        AWSResponseBase.model_validate(response).check()

    def batch_delete(self, keys: list[str]):
        if keys is None or len(keys) == 0:
            return
        response = self.s3_client.delete_objects(Bucket=self.bucket, Delete=dict(Objects=[dict(Key=key) for key in keys]))
        AWSResponseBase.model_validate(response).check()

    def list_all(self) -> list[AWSS3Object]:
        response = self.s3_client.list_objects_v2(Bucket=self.bucket)
        response = AWSS3ListResponse.model_validate(response)
        response.check()
        return response.Contents

    def list_page(self, page_size: int = 100) -> Generator[AWSS3Object, None, None]:
        continuation_token = None
        while True:
            kwargs = dict(Bucket=self.bucket, MaxKeys=page_size)
            if continuation_token:
                kwargs.update(ContinuationToken=continuation_token)
            response = self.s3_client.list_objects_v2(**kwargs)

            response = AWSS3ListResponse.model_validate(response)
            if response.ResponseMetadata.HTTPStatusCode != http_status.HTTP_200_OK:
                log.warning(f'Failed to list objects: {response.ResponseMetadata}')
                continue

            yield from response.Contents
            if not response.IsTruncated:
                break
            continuation_token = response.NextContinuationToken


aws_s3_client = boto3.client(AWSConst.S3)
oss_public = AWSS3Storage(aws_s3_client, StorageConfig.bucket)
oss_private = AWSS3Storage(aws_s3_client, StorageConfig.private_bucket)
