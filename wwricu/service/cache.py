import asyncio


async def timeout(key: str, second: int):
    await asyncio.sleep(second)
    await cache_delete(key)


async def cache_delete(key: str):
    cache_data.pop(key)
    if task := timeout_callback.pop(key, None):
        task.cancel()


async def cache_set(key: str, value: any, second: int | None = 600):
    if task := timeout_callback.pop(key, None):
        task.cancel()
    cache_data[key] = value
    if second is not None and second > 0:
        timeout_callback[key] = asyncio.create_task(timeout(key, second))


async def cache_get(key: str) -> any:
    return cache_data.get(key)


cache_data: dict[str, any] = dict()
timeout_callback: dict[str, asyncio.Task] = dict()
