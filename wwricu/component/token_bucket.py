import time

from wwricu.component.cache import Cache, bucket_cache
from wwricu.domain.common import TokenBucketState
from wwricu.domain.enum import CacheKeyEnum


class TokenBucketLimiter:
    name: str
    cache: Cache
    capacity: float
    speed: float
    expiration: int

    def __init__(self, name: str, speed: float, capacity: float):
        if capacity <= 0 or speed <= 0:
            raise ValueError
        self.name = name
        self.cache = bucket_cache
        self.capacity = capacity
        self.speed = speed
        self.expiration = max(int(capacity / speed), 60)

    async def allow(self, bucket_id: str, qps: float | int = 1.0) -> bool:
        if not qps:
            return True

        now = time.time()
        key = CacheKeyEnum.TOKEN_BUCKET.format(name=self.name, id=bucket_id)
        state = await self.cache.get(key)
        if not isinstance(state, TokenBucketState):
            state = TokenBucketState(tokens=self.capacity, updated_at=now)

        tokens = min(self.capacity, state.tokens + max(0.0, now - state.updated_at) * self.speed)
        cost = self.speed / qps
        if allowed := tokens >= cost:
            tokens -= cost
        await self.cache.set(key, TokenBucketState(tokens=tokens, updated_at=now), self.expiration)
        return allowed


rate_limiter = TokenBucketLimiter('default', 100.0, 150.0)
