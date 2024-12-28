import io

from fastapi import HTTPException, status
from qiniu import Auth, put_data, BucketManager

from wwricu.config import StorageConfig
from wwricu.domain.common import StorageConstant, HttpErrorDetail


async def storage_put(key: str, data: io.BytesIO) -> str:
    token = client.upload_token(StorageConfig.bucket, key)
    ret, response = put_data(token, key, data)
    if ret.get(StorageConstant.RET_KEY) != key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=HttpErrorDetail.UPLOAD_FAILURE)
    return f'{StorageConfig.domain}/{key}'


async def storage_delete(key: str) -> bool:
    bucket = BucketManager(client)
    return bucket.delete(StorageConfig.bucket, key) is None


client = Auth(StorageConfig.access_key, StorageConfig.security_key)
