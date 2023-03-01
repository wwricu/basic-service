import asyncio
import io
import sys

import uvicorn
from anyio import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apis import router
from config import Config, logger
from dao import AsyncDatabase, AsyncRedis
from service import HTTPService, MailService


app = FastAPI()


def schedule_jobs():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        MailService.daily_mail,
        CronTrigger(hour=8, timezone='Asia/Shanghai'),
    )
    scheduler.add_job(
        HTTPService.parse_bing_image_url,
        CronTrigger(hour=9, timezone='Asia/Shanghai'),
    )
    scheduler.start()
    logger.info('schedule jobs started')


@app.on_event('startup')
async def startup():
    # print() cannot print every unicode character, change to uft-8 under windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

    await Config.init_config()
    await asyncio.gather(
        AsyncDatabase.init_database(),
        AsyncRedis.init_redis()
    )
    schedule_jobs()

    path = Path(Config.static.content_path)
    if not await Path.exists(path):
        await Path.mkdir(path)

    app.include_router(router)
    app.mount(
        f'/{Config.static.root_path}',
        StaticFiles(directory=Config.static.root_path),
        name=Config.static.root_path
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex='https?://.*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['X-token-need-refresh', 'X-content-id']
    )


@app.on_event('shutdown')
async def shutdown():
    await asyncio.gather(
        AsyncRedis.close(),
        AsyncDatabase.close()
    )
    logger.info('see u later')


if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        host='0.0.0.0',
        port=8000,
        log_level='info'
    )
