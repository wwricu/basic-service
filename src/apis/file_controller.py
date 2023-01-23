import asyncio
import hashlib
import os

from anyio import Path
from fastapi import APIRouter, Depends,  HTTPException, Request, UploadFile

from service import RequiresRoles


file_router = APIRouter(prefix="/file", tags=["file"])


@file_router.post(
    "/static/content", dependencies=[Depends(RequiresRoles('admin'))]
)
async def upload(files: list[UploadFile], request: Request):
    succ_files, content_id = [], request.headers['x-content-id']
    if content_id is None:
        raise HTTPException(status_code=404, detail='no content id')

    content_path = Path(f'static/content/{content_id}')
    if not await Path.exists(content_path):
        await Path.mkdir(content_path)

    async def save_file(file: UploadFile):
        suffix = os.path.splitext(file.filename)[-1]
        filename = hashlib.md5(
            file.filename.encode(encoding='utf-8')
        ).hexdigest()
        path = f'{content_path}/{filename}{suffix}'
        await Path(path).write_bytes(await file.read())
        if os.path.exists(path):
            succ_files.append({
                'name': file.filename,
                'path': path
            })

    async_tasks = []
    for f in files:
        async_tasks.append(save_file(f))
    await asyncio.gather(*async_tasks)
    return {'files': succ_files}
