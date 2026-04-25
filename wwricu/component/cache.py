import asyncio
import shelve
import time
from collections import OrderedDict
from typing import Protocol, Any

from loguru import logger as log


class LocalCache:
    # NOTE: all functions in this class has no await inside so they are atomic in a coroutine context, no lock needed
    name: str
    data: OrderedDict[str, Any]
    max_size: int
    persist: bool
    expiration: dict[str, int]
    heartbeat: asyncio.Task | None

    def __init__(self, name: str, max_size: int = 10000, persist: bool = False):
        now = time.time()
        self.name = name
        self.max_size = max_size
        self.heartbeat = None
        self.persist = persist if not __debug__ else False

        if not self.persist:
            self.data = OrderedDict()
            self.expiration = {}
            return

        with shelve.open(self.name) as shv:
            self.data, self.expiration = shv.get(self.name, (OrderedDict(), {}))
        for key in [key for key, expire in self.expiration.items() if 0 < expire < now]:
            self.data.pop(key, None)
            self.expiration.pop(key, None)
        log.info(f'{len(self.data)} {self.name} cache entries loaded')

    async def clear_expired(self):
        while True:
            await asyncio.sleep(1)
            now = time.time()
            '''
            NOTE: (... for ... in ...) is a generator expression while [... for ... in ...] is a comprehension
            a generator expression would generate elements on iterating, comprehension create the iteration in advance.
            '''
            for key in [key for key, expire in self.expiration.items() if 0 < expire <= now]:
                self.data.pop(key, None)
                self.expiration.pop(key, None)

    async def get(self, key: str | None) -> Any:
        if not isinstance(key, str) or key not in self.data:
            return None

        if 0 < self.expiration.get(key, 0) <= time.time():
            self.data.pop(key, None)
            self.expiration.pop(key, None)
            return None

        self.data.move_to_end(key)
        return self.data[key]

    async def set(self, key: str | None, value: Any, second: int = 600):
        if not isinstance(key, str):
            raise KeyError(key)

        if self.heartbeat is None or self.heartbeat.done():
            self.heartbeat = asyncio.create_task(self.clear_expired())

        if second > 0:
            self.expiration[key] = int(time.time()) + second
        self.data[key] = value
        self.data.move_to_end(key)

        if len(self.data) > self.max_size:
            evicted_key, _ = self.data.popitem(last=False)
            self.expiration.pop(evicted_key, None)

    async def delete(self, key: str | None):
        if not isinstance(key, str) or key not in self.data:
            return
        self.data.pop(key, None)
        self.expiration.pop(key, None)

    async def delete_all(self):
        self.data.clear()
        self.expiration.clear()

    async def close(self):
        if self.heartbeat and not self.heartbeat.done():
            self.heartbeat.cancel()
        if not self.persist:
            return
        with shelve.open(self.name) as shv:
            shv.clear()
            shv[self.name] = (self.data, self.expiration)
            log.info(f'{len(self.data)} cache entries dumped')


class Cache(Protocol):
    async def get(self, key: str | None) -> Any:...

    async def set(self, key: str | None, value: Any, second: int = 600):...

    async def delete(self, key: str | None):...

    async def delete_all(self):...

    async def close(self):...

sys_cache: Cache = LocalCache(name='sys', persist=True)
query_cache: Cache = LocalCache(name='query')
post_cache: Cache = LocalCache(name='post')
