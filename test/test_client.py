from fastapi.testclient import TestClient

from wwricu.api import api_router
from wwricu.main import app


app.include_router(api_router)
client = TestClient(app)
