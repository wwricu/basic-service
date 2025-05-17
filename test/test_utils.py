from random import Random

from fastapi.testclient import TestClient

from wwricu.main import app


client = TestClient(app)
random = Random()
