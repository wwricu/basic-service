import time

from wwricu.component.cache import Cache, bucket_cache
from wwricu.config import app_config
from wwricu.domain.common import TokenBucketState
from wwricu.domain.enum import CacheKeyEnum


class TokenBucket:
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
        return await self.cost(bucket_id, self.speed / qps)

    async def cost(self, bucket_id: str, cost: float | int) -> bool:
        now = time.time()
        key = CacheKeyEnum.TOKEN_BUCKET.format(name=self.name, id=bucket_id)

        if (state := await self.cache.get(key)) is None:
            state = TokenBucketState(tokens=self.capacity, updated_at=now)

        tokens = min(self.capacity, state.tokens + max(0.0, now - state.updated_at) * self.speed)
        if allowed := tokens >= cost:
            tokens -= cost
        await self.cache.set(key, TokenBucketState(tokens=tokens, updated_at=now), self.expiration)
        return allowed

    async def reset(self, bucket_id: str):
        await self.cache.delete(CacheKeyEnum.TOKEN_BUCKET.format(name=self.name, id=bucket_id))


default_bucket = TokenBucket(name='default', speed=100.0, capacity=150.0)
login_ip_bucket = TokenBucket(name='login', speed=1.0, capacity=app_config.security.login_ip_span)
