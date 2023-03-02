import asyncio
import functools
import os
import sys
import time

from fastapi.testclient import TestClient

sys.path.append(rf'{os.getcwd()}\src')
from main import app, startup


client = TestClient(app)
asyncio.run(startup())


def test_method(method: callable) -> callable:
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        print(f'-------------- {method.__name__} test begins --------------')
        begin = time.time()
        res = method(*args, **kwargs)
        print(
            '--{name} test ends, {time} seconds elapsed --'
            .format(
                name=method.__name__,
                time=time.time() - begin
            )
        )
        return res
    return wrapper
