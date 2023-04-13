import asyncio
import io
import sys

import uvicorn
from anyio import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apis import router
from config import Config, logger
from dao import AsyncDatabase, AsyncRedis
from service import schedule_jobs, SqlAdmin


app = FastAPI(version='1.0.0')


@app.on_event('startup')
async def startup():
    # print() cannot print every unicode character under unicode windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

    await Config.init_config()
    await asyncio.gather(
        AsyncDatabase.init_database(),
        AsyncRedis.init_redis()
    )
    await SqlAdmin.init(app)
    schedule_jobs()

    if not await Path.exists(path := Path(Config.static.content_path)):
        await Path.mkdir(path)

    app.include_router(router)
    app.mount(
        f'/{Config.static.root_path}',
        StaticFiles(directory=Config.static.root_path),
        name=Config.static.root_path
    )
    app.add_middleware(CORSMiddleware, **Config.middleware.__dict__)


@app.on_event('shutdown')
async def shutdown():
    await asyncio.gather(AsyncRedis.close_connection(), AsyncDatabase.close())
    logger.info('see u later')


if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0', port=8000, log_level='info')
