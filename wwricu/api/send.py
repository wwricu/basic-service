import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, UploadFile
from fastapi.responses import FileResponse

from wwricu.domain.constant import CommonConstant, StringTemplate
from wwricu.domain.enum import EnvVarEnum
from wwricu.service.security import hmac_sign

send_api = APIRouter(prefix='/send', tags=['Common API'])
file_dir: Path = Path(EnvVarEnum.UPLOAD_FILE_DIR.get())


@send_api.post('/upload', response_model=str)
async def upload(upload_file: UploadFile) -> str:
    # TODO: OTP, space limitation, password, trace in db.
    if upload_file.size >= CommonConstant.UPLOAD_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    location = uuid.uuid4().hex
    expire = int(time.time()) + 7 * 24 * 60 * 60
    file_url = StringTemplate.file_url.format(filename=upload_file.filename, location=location, expire=expire)

    file_dir.mkdir(parents=True, exist_ok=True)
    file = file_dir / location
    with file.open('wb+') as f:
        f.write(await upload_file.read())

    return StringTemplate.presigned_url.format(url=file_url, signature=hmac_sign(file_url))


@send_api.get('/download', response_class=FileResponse)
async def download(filename: str, location: str, expire: int, signature: str) -> FileResponse:
    file_url = StringTemplate.file_url.format(filename=filename, location=location, expire=expire)
    if signature != hmac_sign(file_url):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if expire > int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    file = file_dir / location
    if not file.exists() or not file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        status_code=status.HTTP_200_OK,
        path=str(file.absolute()),
        filename=filename,
        media_type='application/octet-stream'
    )
