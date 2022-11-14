from fastapi import FastAPI, HTTPException
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


@app.router.get("/test")
def test():
    try:
        print('here')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail=e.__str__())
