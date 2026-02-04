import asyncio
import shelve
import time
from typing import Protocol, Any

from loguru import logger as log


class LocalCache:
    # NOTE: all functions in this class has no await inside so they are atomic in a coroutine context, no lock needed
    cache_data: dict[str, Any]
    timeout_callback: dict[str, asyncio.Task]
    cache_name: str = 'cache'

    def __init__(self):
        self.timeout_callback = {}
        with shelve.open(self.cache_name) as shv:
            self.cache_data = shv.get(self.cache_name, {})
        '''
        NOTE: (... for ... in ...) is a generator expression while [... for ... in ...] is a comprehension
        a generator expression would generate elements on iterating, comprehension create the iteration in advance.
        '''
        now = time.time()
        for key in [key for key, (_, expire) in self.cache_data.items() if 0 < expire < now]:
            self.cache_data.pop(key, None)
        log.info(f'{len(self.cache_data)} cache entries loaded')

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        _ = self.timeout_callback.pop(key, None)
        self.cache_data.pop(key, None)

    async def get(self, key: str) -> Any:
        if not isinstance(key, str):
            return None
        value, expire = self.cache_data.get(key, (None, 0))
        if 0 < expire < time.time():
            self.cache_data.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, second: int = 600):
        if not isinstance(key, str):
            raise ValueError(key)
        if task := self.timeout_callback.pop(key, None):
            task.cancel()

        self.cache_data[key] = value, time.time() + second if second > 0 else 0
        if second > 0:
            self.timeout_callback[key] = asyncio.create_task(self.timeout(key, second))

    async def delete(self, key: str):
        if task := self.timeout_callback.pop(key, None):
            task.cancel()
        self.cache_data.pop(key, None)

    async def close(self):
        with shelve.open(self.cache_name) as shv:
            shv.clear()
            shv[self.cache_name] = self.cache_data
            log.info(f'{len(self.cache_data)} cache entries dumped')


class Cache(Protocol):
    async def get(self, key: str) -> Any:...

    async def set(self, key: str, value: Any, second: int = 600):...

    async def delete(self, key: str):...

    async def close(self):...


cache: Cache = LocalCache()
