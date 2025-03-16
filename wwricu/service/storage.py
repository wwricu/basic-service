import boto3

from wwricu.config import StorageConfig
from wwricu.domain.third import AWSConst, AWSS3ListResponse,  AWSS3Object, AWSS3Response


class AWSS3Storage:
    def __init__(self):
        self.s3_client = boto3.client(AWSConst.S3, region_name=AWSConst.REGION)

    def get(self, key: str, bucket: str = StorageConfig.bucket) -> bytes | None:
        # If S3 object_name was not specified, use file_name
        result_dict: dict = self.s3_client.get_object(Bucket=bucket, Key=key)
        response = AWSS3Response.model_validate(result_dict)
        return response.Body.read()

    def put(self, key: str, data: bytes, bucket: str = StorageConfig.bucket) -> str:
        self.s3_client.put_object(Bucket=bucket, Key=key, Body=data)
        return f'https://{AWSConst.S3}.{StorageConfig.region}.{AWSConst.AWS_DOMAIN}/{bucket}/{key}'

    def delete(self, key: str, bucket: str = StorageConfig.bucket):
        self.s3_client.delete_object(Bucket=bucket, Key=key)

    def batch_delete(self, keys: list[str], bucket: str = StorageConfig.bucket):
        self.s3_client.delete_objects(Bucket=bucket, Delete=dict(Objects=[dict(Key=key) for key in keys]))

    def list_all(self, bucket: str = StorageConfig.bucket) -> list[AWSS3Object]:
        response = self.s3_client.list_objects_v2(Bucket=bucket)
        response = AWSS3ListResponse.model_validate(response)
        return response.Contents


oss = AWSS3Storage()
