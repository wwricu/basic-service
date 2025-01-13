import boto3

from wwricu.config import StorageConfig
from wwricu.domain.third import AWSS3Response, AWSConst


def get_object(key: str) -> bytes | None:
    # If S3 object_name was not specified, use file_name
    result_dict: dict = s3_client.get_object(Bucket=StorageConfig.bucket, Key=key)
    response = AWSS3Response.model_validate(result_dict)
    return response.Body.read()


def put_object(key: str, data: bytes) -> str:
    s3_client.put_object(Bucket=StorageConfig.bucket, Key=key, Body=data)
    return f'https://{StorageConfig.s3}.{StorageConfig.region}.{AWSConst.aws_domain}/{StorageConfig.bucket}/{key}'


def delete_object(key: str):
    s3_client.delete_object(Bucket=StorageConfig.bucket, Key=key)


s3_client = boto3.client(AWSConst.s3, region_name=StorageConfig.region)
