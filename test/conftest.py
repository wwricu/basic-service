import pytest

from test.test_utils import client


@pytest.fixture(scope='session', autouse=True)
def app_running():
    # The engine and the caches are built inside the lifespan, so the shared client has to be entered
    # once per run; without this every request dies on 'database has no attribute scoped_session'.
    with client:
        yield
