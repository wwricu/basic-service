import asyncio


def cache_delete(key: str):
    if key in cache_data:
        del cache_data[key]


async def timeout(key: str, second: int):
    await asyncio.sleep(second)
    cache_delete(key)


def cache_set(key: str, value: any, second: int = 600):
    cache_data[key] = value
    if second > 0:
        asyncio.create_task(second)


def cache_get(key: str) -> any:
    return cache_data.get(key)


cache_data: dict = dict()
