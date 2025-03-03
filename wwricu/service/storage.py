import boto3

from wwricu.config import StorageConfig
from wwricu.domain.third import AWSConst, AWSS3ListResponse,  AWSS3Object, AWSS3Response


def get_object(key: str, bucket: str = StorageConfig.bucket) -> bytes | None:
    # If S3 object_name was not specified, use file_name
    result_dict: dict = s3_client.get_object(Bucket=bucket, Key=key)
    response = AWSS3Response.model_validate(result_dict)
    return response.Body.read()


def put_object(key: str, data: bytes, bucket: str = StorageConfig.bucket) -> str:
    s3_client.put_object(Bucket=bucket, Key=key, Body=data)
    return f'https://{AWSConst.s3}.{StorageConfig.region}.{AWSConst.aws_domain}/{bucket}/{key}'


def delete_object(key: str, bucket: str = StorageConfig.bucket):
    s3_client.delete_object(Bucket=bucket, Key=key)


def delete_objects(keys: list[str], bucket: str = StorageConfig.bucket):
    response = s3_client.delete_objects(Bucket=bucket, Delete=dict(Objects=[dict(Key=key) for key in keys]))
    print(response)


def list_all_objects(bucket: str = StorageConfig.bucket) -> list[AWSS3Object]:
    response = s3_client.list_objects_v2(Bucket=bucket)
    response = AWSS3ListResponse.model_validate(response)
    return response.Contents


s3_client = boto3.client(AWSConst.s3, region_name=StorageConfig.region)
