import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from service import DatabaseService
from apis import router
from config import Config

Config.read_config()

DatabaseService.init_db()

app = FastAPI()

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_origin_regex='https?://.*',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['X-token-need-refresh', 'X-content-id']
)

if not os.path.exists('static'):
    os.makedirs('static')
app.mount("/static", StaticFiles(directory="static"), name="static")
