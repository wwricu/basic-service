import asyncio
import hashlib

from anyio import Path
from fastapi import APIRouter, Depends,  HTTPException, Request, UploadFile

from config import Config, logger
from service import RoleRequired


file_router = APIRouter(prefix='/file', tags=['file'])


@file_router.post(
    '/static/content', dependencies=[Depends(RoleRequired('admin'))]
)
async def upload(files: list[UploadFile], request: Request):
    success_files, content_id = [], request.headers['x-content-id']
    if content_id is None:
        raise HTTPException(status_code=404, detail='no content id')

    content_path = Path(f'{Config.static.content_path}/{content_id}')
    if not await Path.exists(content_path):
        await Path.mkdir(content_path)

    async def save_file(file: UploadFile):
        suffix = Path(file.filename).suffix
        filename = hashlib.md5(
            file.filename.encode(encoding='utf-8')
        ).hexdigest()
        # Path.__fspath__()/__str__() aka original Path._path
        path = Path(f'{content_path.__fspath__()}/{filename}{suffix}')
        await path.write_bytes(await file.read())
        if await Path.exists(path):
            success_files.append({
                'name': file.filename,
                'path': path.__fspath__()
            })

    async_tasks = []
    for f in files:
        async_tasks.append(save_file(f))
    await asyncio.gather(*async_tasks)
    return {'files': success_files}
