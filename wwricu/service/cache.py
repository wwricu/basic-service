import asyncio
import shelve
import time
from collections import OrderedDict
from typing import Protocol, Any

from loguru import logger as log


class LocalCache:
    # NOTE: all functions in this class has no await inside so they are atomic in a coroutine context, no lock needed
    cache_data: OrderedDict[str, Any]
    timeout_callback: dict[str, asyncio.Task]
    max_size: int
    cache_name: str = 'cache'

    def __init__(self, max_size: int = 100000):
        now = time.time()
        self.max_size = max_size
        self.timeout_callback = {}
        with shelve.open(self.cache_name) as shv:
            self.cache_data = shv.get(self.cache_name, OrderedDict())
        '''
        NOTE: (... for ... in ...) is a generator expression while [... for ... in ...] is a comprehension
        a generator expression would generate elements on iterating, comprehension create the iteration in advance.
        '''
        for key in [key for key, (_, expire) in self.cache_data.items() if 0 < expire < now]:
            self.cache_data.pop(key, None)
        log.info(f'{len(self.cache_data)} cache entries loaded')

    def cancel_timeout_task(self, key: str):
        if task := self.timeout_callback.pop(key, None):
            task.cancel()

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        _ = self.timeout_callback.pop(key, None)
        self.cache_data.pop(key, None)

    async def get(self, key: str) -> Any:
        if not isinstance(key, str) or key not in self.cache_data:
            return None

        value, expire = self.cache_data.get(key, (None, 0))
        if 0 < expire < time.time():
            self.cancel_timeout_task(key)
            self.cache_data.pop(key, None)
            return None

        self.cache_data.move_to_end(key)
        return value

    async def set(self, key: str, value: Any, second: int = 600):
        if not isinstance(key, str):
            raise ValueError(key)
        self.cancel_timeout_task(key)

        self.cache_data[key] = value, time.time() + second if second > 0 else 0
        self.cache_data.move_to_end(key)
        if second > 0:
            self.timeout_callback[key] = asyncio.create_task(self.timeout(key, second))

        if len(self.cache_data) > self.max_size:
            # use sync funcs to ensure deletion atomic
            lru_key, _ = self.cache_data.popitem(last=False)
            self.cancel_timeout_task(lru_key)

    async def delete(self, key: str):
        self.cancel_timeout_task(key)
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
