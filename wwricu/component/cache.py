from __future__ import annotations
import asyncio
import shelve
import time
from collections import OrderedDict
from typing import Protocol, Any

from loguru import logger as log

from wwricu.domain.constant import TimeConstant


class LocalCache:
    # NOTE: all functions in this class has no await inside so they are atomic in a coroutine context, no lock needed
    name: str
    data: OrderedDict[str, Any]
    max_size: int
    persist: bool
    expiration: dict[str, int]

    heartbeat: asyncio.Task | None = None
    all_caches: dict[str, LocalCache] = {}

    def __init__(self, name: str, max_size: int = 10000, persist: bool = False):
        self.name = name
        self.max_size = max_size
        self.heartbeat = None
        self.persist = persist if not __debug__ else False

        if LocalCache.all_caches.get(self.name) is not None:
            raise KeyError(self.name)
        LocalCache.all_caches[self.name] = self

        if not self.persist:
            self.data = OrderedDict()
            self.expiration = {}
            return

        with shelve.open(self.name) as shv:
            self.data, self.expiration = shv.get(self.name, (OrderedDict(), {}))
        log.info(f'{len(self.data)} {self.name} cache entries loaded')

    async def get(self, key: str | None) -> Any:
        if not isinstance(key, str) or key not in self.data:
            return None

        if 0 < self.expiration.get(key, 0) <= time.time():
            del self.data[key]
            self.expiration.pop(key, None)
            return None

        self.data.move_to_end(key)
        return self.data[key]

    async def set(self, key: str | None, value: Any, second: int = TimeConstant.CACHE_EXPIRATION):
        if not isinstance(key, str):
            raise KeyError(key)

        if LocalCache.heartbeat is None or LocalCache.heartbeat.done():
            LocalCache.heartbeat = asyncio.create_task(LocalCache.clean())

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
        del self.data[key]
        self.expiration.pop(key, None)

    async def delete_all(self):
        self.data.clear()
        self.expiration.clear()

    async def close(self):
        LocalCache.all_caches.pop(self.name, None)
        if len(LocalCache.all_caches) == 0 and LocalCache.heartbeat and not LocalCache.heartbeat.done():
            LocalCache.heartbeat.cancel()
            try:
                await LocalCache.heartbeat
            except asyncio.CancelledError:
                pass
        if not self.persist:
            return
        with shelve.open(self.name) as shv:
            shv.clear()
            shv[self.name] = (self.data, self.expiration)
            log.info(f'{len(self.data)} cache entries dumped')

    @classmethod
    async def clean(cls):
        while True:
            await asyncio.sleep(10)
            now = time.time()
            '''
            NOTE: (... for ... in ...) is a generator expression while [... for ... in ...] is a comprehension
            a generator expression would generate elements on iterating, comprehension create the iteration in advance.
            '''
            for cache in cls.all_caches.values():
                for key in [key for key, expire in cache.expiration.items() if 0 < expire <= now]:
                    cache.data.pop(key, None)
                    del cache.expiration[key]

    @classmethod
    async def shutdown(cls):
        for cache in list(cls.all_caches.values()):
            try:
                await cache.close()
            except Exception as e:
                log.error(f'Failed to close cache {cache.name} {e}')


class Cache(Protocol):
    async def get(self, key: str | None) -> Any:...

    async def set(self, key: str | None, value: Any, second: int = TimeConstant.CACHE_EXPIRATION):...

    async def delete(self, key: str | None):...

    async def delete_all(self):...

    async def close(self):...


sys_cache: Cache = LocalCache(name='sys', persist=True)
query_cache: Cache = LocalCache(name='query')
post_cache: Cache = LocalCache(name='post')
bucket_cache = LocalCache(name='bucket', max_size=100000)
