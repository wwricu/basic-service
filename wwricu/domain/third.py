from datetime import datetime

from botocore.response import StreamingBody
from pydantic import ConfigDict

from wwricu.domain.common import BaseModel


class AWSConst(object):
    S3: str = 's3'
    APP_CONFIG_DATA: str = 'appconfigdata'
    REGION = 'us-west-2'
    AWS_DOMAIN = 'amazonaws.com'


class AWSS3ResponseMetaData(BaseModel):
    RequestId: str
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


class AWSS3Object(BaseModel):
    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str


class AWSS3ListResponse(BaseModel):
    ResponseMetadata: AWSS3ResponseMetaData
    IsTruncated: bool
    Contents: list[AWSS3Object]
    Name: str
    Prefix: str
    MaxKeys: int
    EncodingType: str
    KeyCount: int
    NextContinuationToken: str | None = None


class AWSAppConfigSessionResponse(BaseModel):
    ResponseMetadata: AWSS3ResponseMetaData
    InitialConfigurationToken: str


class AWSAppConfigConfigResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ResponseMetadata: AWSS3ResponseMetaData
    NextPollConfigurationToken: str
    NextPollIntervalInSeconds: int
    ContentType: str
    VersionLabel: str | None = None
    Configuration: StreamingBody
