from datetime import datetime
from typing import Literal

from botocore.response import StreamingBody
from fastapi import HTTPException
from pydantic import ConfigDict

from wwricu.domain.common import BaseModel


class CloudflareConst:
    R2: Literal['s3'] = 's3'
    R2_REGION: str = 'auto'
    R2_ENDPOINT: str = 'https://{account_id}.r2.cloudflarestorage.com'
    GET_OBJECT: str = 'get_object'


class AWSResponseMetaData(BaseModel):
    RequestId: str = ''  # Cloudflare R2 omits RequestId in ResponseMetadata on some operations
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
