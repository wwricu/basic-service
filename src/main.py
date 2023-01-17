import os
import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from service import DatabaseService
from apis import router
from config import Config


app = FastAPI()


@app.on_event('startup')
async def startup():
    Config.read_config()
    DatabaseService.init_db()
    try:
        os.makedirs('static/content')
    except FileExistsError:
        pass

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


if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                log_level="info")
