import math
import time

from wwricu.component.cache import Cache, LocalCache
from wwricu.domain.common import TokenBucketState
from wwricu.domain.enum import CacheKeyEnum


class TokenBucketLimiter:
    name: str
    cache: Cache
    capacity: float
    refill_speed: float
    refill_seconds: int

    def __init__(self, name: str, capacity: float, refill_speed: float):
        if capacity <= 0 or refill_speed <= 0:
            raise ValueError
        self.name = name
        self.cache = bucket_cache
        self.capacity = capacity
        self.refill_speed = refill_speed
        self.refill_seconds = math.ceil(capacity / refill_speed)

    async def allow(self, bucket_id: str, cost: float | int = 1.0) -> bool:
        now = time.time()
        key = CacheKeyEnum.TOKEN_BUCKET.format(name=self.name, id=bucket_id)
        state = await self.cache.get(key)
        if not isinstance(state, TokenBucketState):
            state = TokenBucketState(tokens=self.capacity, updated_at=now)

        tokens = min(self.capacity, state.tokens + max(0.0, now - state.updated_at) * self.refill_speed)
        if allowed := tokens >= cost:
            tokens -= cost
        await self.cache.set(key, TokenBucketState(tokens=tokens, updated_at=now), self.refill_seconds)
        return allowed


bucket_cache = LocalCache(name='bucket', max_size=10000)
