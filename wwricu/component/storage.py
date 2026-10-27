import asyncio

import boto3
from mypy_boto3_s3 import S3Client

from wwricu.config import StorageConfig, app_config, env
from wwricu.domain.third import AWSS3Response, AWSResponseBase, CloudflareConst


class R2Storage:
    bucket: str
    s3_client: S3Client

    @property
    def resource_api(self) -> str:
        return f'https://{env.resource_domain}/image/'

    def __init__(self, config: StorageConfig):
        self.bucket = config.bucket
        # Cloudflare R2 speaks the S3 protocol, so boto3 needs the account-scoped R2 endpoint explicitly.
        # Credentials are read from the config file (StorageConfig) and injected straight into the client.
        self.s3_client = boto3.client(
            CloudflareConst.R2,
            endpoint_url=(CloudflareConst.R2_ENDPOINT.format(account_id=env.CF_ACCOUNT_ID)),
            region_name=CloudflareConst.R2_REGION,
            aws_access_key_id=config.access_key_id or None,
            aws_secret_access_key=config.secret_access_key or None,
        )

    def sync_get(self, key: str) -> bytes:
        # If S3 object_name was not specified, use file_name
        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        s3_resp = AWSS3Response.model_validate(response)
        s3_resp.check()
        with s3_resp.Body:
            return s3_resp.Body.read()

    def sync_put(self, key: str, data: bytes) -> str:
        response = self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=data)
        AWSResponseBase.model_validate(response).check()
        return f'{self.resource_api}{key}'

    def sync_delete(self, key: str):
        response = self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        AWSResponseBase.model_validate(response).check()

    def generate_presigned_url(self, key: str, expires: int) -> str:
        return self.s3_client.generate_presigned_url(
            CloudflareConst.GET_OBJECT,
            Params=dict(Bucket=self.bucket, Key=key),
            ExpiresIn=expires
        )

    def get_key_from_url(self, url: str) -> str | None:
        if not url or not url.startswith(self.resource_api):
            return None
        url = url.strip()
        return url.removeprefix(self.resource_api)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self.sync_get, key)

    async def put(self, key: str, data: bytes) -> str:
        return await asyncio.to_thread(self.sync_put, key, data)

    async def delete(self, key: str):
        await asyncio.to_thread(self.sync_delete, key)


storage = R2Storage(app_config.storage)
