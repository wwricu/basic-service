from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from service import DatabaseService
from apis import router

DatabaseService.init_db()

app = FastAPI()

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
