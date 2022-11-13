from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from service import DatabaseService
from apis import router

DatabaseService.init_db()

app = FastAPI()

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)
