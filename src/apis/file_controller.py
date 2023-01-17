import os
import hashlib
from fastapi import Depends, APIRouter, UploadFile, Request, HTTPException
from .auth_controller import RequiresRoles


file_router = APIRouter(prefix="/file", tags=["file"])


@file_router.post("/static/content",
                  dependencies=[Depends(RequiresRoles('admin'))])
async def upload(files: list[UploadFile], request: Request):
    succ_files, content_id = [], request.headers['x-content-id']
    if content_id is None:
        raise HTTPException(status_code=404, detail='no content id')

    content_path = f'static/content/{content_id}'
    if not os.path.exists(content_path):
        os.makedirs(content_path)

    for file in files:
        data = await file.read()
        suffix = os.path.splitext(file.filename)[-1]
        filename = hashlib.md5(os.path.splitext(file.filename)[0]
                                 .encode(encoding='utf-8')).hexdigest()
        path = f'{content_path}/{filename}{suffix}'
        with open(path, 'wb') as f:
            f.write(data)
        if os.path.exists(path):
            succ_files.append({
                'name': file.filename,
                'path': path
            })

    return {'files': succ_files}
