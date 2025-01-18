import asyncio
import pickle
import time

from wwricu.domain.common import CommonConstant


async def timeout(key: str, second: int):
    await asyncio.sleep(second)
    await cache_delete(key)


async def cache_delete(key: str):
    cache_data.pop(key)
    cache_timeout.pop(key)
    if task := timeout_callback.pop(key, None):
        task.cancel()


async def cache_set(key: str, value: any, second: int = 600):
    if second is None or second <= 0:
        second = 600
    if task := timeout_callback.pop(key, None):
        task.cancel()
    cache_data[key] = value
    if second > 0:
        timeout_callback[key] = asyncio.create_task(timeout(key, second))
        cache_timeout[key] = int(time.time()) + second


async def cache_get(key: str) -> any:
    if 0 < cache_timeout.get(key, 0) < int(time.time()):
        return None
    return cache_data.get(key)


async def cache_dump():
    with open(CommonConstant.CACHE_DUMP_FILE, 'wb+') as f:
        f.write(pickle.dumps((cache_data, cache_timeout)))


async def cache_load():
    with open(CommonConstant.CACHE_DUMP_FILE, 'rb') as f:
        persist_data, persist_timeout = pickle.loads(f.read())
    now = int(time.time())
    for key, value in persist_data:
        if (second := persist_timeout.get(key, 0) - now) > 0:
            await cache_set(key, value, second)


cache_data: dict[str, any] = dict()
cache_timeout: dict[str, int] = dict()
timeout_callback: dict[str, asyncio.Task] = dict()
