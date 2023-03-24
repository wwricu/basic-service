import asyncio
import hashlib

from anyio import Path
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile
)

from config import Config
from service import HTTPService, RoleRequired


file_router = APIRouter(prefix='/file', tags=['file'])


@file_router.post(
    '/static/upload',
    dependencies=[Depends(RoleRequired('admin'))]
)
async def upload(files: list[UploadFile], request: Request):
    async_tasks, content_path = [], Path('{path}/{content_id}'.format(
        path=Config.static.content_path,
        content_id=request.headers.get('x-content-id', default='default')
    ))
    if not await Path.exists(content_path):
        await Path.mkdir(content_path)

    for f in files:
        async_tasks.append(save_file(f, content_path, f.filename))
    return {'files': await asyncio.gather(*async_tasks)}


@file_router.post('/static/url', dependencies=[Depends(RoleRequired('admin'))])
async def rewrite_url(request: Request, url: str = Body(embed=True)):
    # embed: expect {"url": "str"} instead of "str"
    content_path = Path('{path}/{content_id}'.format(
        path=Config.static.content_path,
        content_id=request.headers.get('x-content-id', default='default')
    ))
    if not await Path.exists(content_path):
        await Path.mkdir(content_path)

    res = await save_file(
        await HTTPService.get_image(url),
        content_path,
        url.split('/')[-1]
    )
    res.setdefault('url', url)
    return res


async def save_file(file: bytes | UploadFile, path: Path, filename: str):
    """
    :param file: file payload or UploadFile, read it out if later
    :param path:
    Path object of expected parent folder, without leading/tailing slash
    :param filename: original file name with suffix
    :return: {
        "name": "original filename",
        "path": "real filename with relative path"
    }
    """
    if not isinstance(file, bytes):
        file = await file.read()

    file_path = path.joinpath('{real_name}.{suffix}'.format(
        real_name=hashlib.md5(filename.encode(encoding='utf-8')).hexdigest(),
        suffix=filename.split('.')[-1]
    ))
    await file_path.write_bytes(file)
    if not await Path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'failed to upload {filename}'
        )
    # Path.__fspath__()/__str__() aka original Path._path
    return {
        'name': filename,
        'path': file_path.__fspath__()
    }
