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
        self.s3_client = boto3.client(
            CloudflareConst.R2,
            endpoint_url=(CloudflareConst.R2_ENDPOINT.format(account_id=env.CF_ACCOUNT_ID)),
            region_name=CloudflareConst.R2_REGION,
            aws_access_key_id=config.access_key_id or None,
            aws_secret_access_key=config.secret_access_key or None,
        )

    async def get(self, key: str) -> bytes:
        def fetch() -> bytes:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            s3_resp = AWSS3Response.model_validate(response)
            s3_resp.check()
            with s3_resp.Body:
                return s3_resp.Body.read()

        return await asyncio.to_thread(fetch)

    async def put(self, key: str, data: bytes) -> str:
        def upload() -> str:
            response = self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=data)
            AWSResponseBase.model_validate(response).check()
            return f'{self.resource_api}{key}'

        return await asyncio.to_thread(upload)

    async def delete(self, key: str):
        def remove() -> None:
            response = self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            AWSResponseBase.model_validate(response).check()

        await asyncio.to_thread(remove)

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


storage = R2Storage(app_config.storage)
