import pickle
import uvicorn
from anyio import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apis import router
from config import Config, logger
from dao import AsyncDatabase, AsyncRedis


app = FastAPI()


@app.on_event('startup')
async def startup():
    await Config.init_config()
    await AsyncDatabase.init_database()
    await AsyncRedis.init_redis()
    path = Path('static/content')
    if not await Path.exists(path):
        await Path.mkdir(path)

    app.include_router(router)
    app.mount("/static", StaticFiles(directory="static"), name="static")
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
    await AsyncDatabase.close()
    logger.info('see u later')


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
