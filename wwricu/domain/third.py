from datetime import datetime

from botocore.response import StreamingBody
from fastapi import HTTPException, status as http_status
from pydantic import ConfigDict

from wwricu.domain.common import BaseModel


class AWSConst:
    S3: str = 's3'
    APP_CONFIG_DATA: str = 'appconfigdata'
    REGION = 'us-west-2'
    AWS_DOMAIN = 'amazonaws.com'


class AWSResponseMetaData(BaseModel):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: dict
    HostId: str | None = None  # S3
    RetryAttempts: int | None = None # SSM


class AWSResponseBase(BaseModel):
    ResponseMetadata: AWSResponseMetaData

    def check(self):
        if self.ResponseMetadata.HTTPStatusCode // 100 != 2:
            raise HTTPException(status_code=self.ResponseMetadata.HTTPStatusCode)


class AWSS3Response(AWSResponseBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    AcceptRanges: str
    LastModified: datetime
    Body: StreamingBody


class AWSS3Object(BaseModel):
    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str


class AWSS3ListResponse(AWSResponseBase):
    IsTruncated: bool
    Contents: list[AWSS3Object]
    Name: str
    Prefix: str
    MaxKeys: int
    EncodingType: str
    KeyCount: int
    NextContinuationToken: str | None = None

class AWSAppConfigSessionResponse(AWSResponseBase):
    InitialConfigurationToken: str


class AWSAppConfigConfigResponse(AWSResponseBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    NextPollConfigurationToken: str
    NextPollIntervalInSeconds: int
    ContentType: str
    VersionLabel: str | None = None
    Configuration: StreamingBody
