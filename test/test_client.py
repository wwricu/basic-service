from fastapi.testclient import TestClient

from src import app

client = TestClient(app)
