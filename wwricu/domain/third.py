from datetime import datetime

from botocore.response import StreamingBody
from pydantic import ConfigDict

from wwricu.domain.common import BaseModel


class AWSConst(object):
    s3: str = 's3'
    ssm: str = 'ssm'
    region = 'us-west-2'
    aws_domain = 'amazonaws.com'
    CONFIG: str = '/basic-service/{env}/config.json'
    AWS_ACCESS_KEY_ID: str = 'AWS_ACCESS_KEY_ID'
    AWS_SECRET_ACCESS_KEY: str = 'AWS_SECRET_ACCESS_KEY'


class AWSS3ResponseMetaData(BaseModel):
    RequestId: str
    HostId: str
    HTTPStatusCode: int
    HTTPHeaders: dict
    HostId: str | None = None  # S3
    RetryAttempts: int | None = None # SSM


class AWSS3Response(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ResponseMetadata: dict
    AcceptRanges: str
    LastModified: datetime
    Body: StreamingBody


class AWSSSMParameter(BaseModel):
    Name: str
    Type: str
    Value: str
    Version: int
    LastModifiedDate: datetime
    ARN: str
    DataType: str


class AWSSSMResponse(BaseModel):
    ResponseMetadata: AWSS3ResponseMetaData
    Parameter: AWSSSMParameter
