import pytest
from fastapi.testclient import TestClient

from wwricu.main import app

client = TestClient(app)

@pytest.fixture(scope='session', autouse=True)
def app_running():
    # The engine and the caches are built inside the lifespan, so the shared client has to be entered
    # once per run; without this every request dies on 'database has no attribute scoped_session'.
    with client:
        yield