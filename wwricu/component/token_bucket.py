import time

from wwricu.component.cache import Cache, bucket_cache
from wwricu.config import app_config
from wwricu.domain.common import TokenBucketState
from wwricu.domain.enum import CacheKeyEnum


class TokenBucketLimiter:
    name: str
    cache: Cache
    capacity: float
    qps: float
    expiration: int

    def __init__(self, name: str, qps: float, capacity: float, enable: bool = True):
        if capacity <= 0 or qps <= 0:
            raise ValueError
        self.name = name
        self.enable = enable
        self.cache = bucket_cache
        self.capacity = capacity
        self.qps = qps
        self.expiration = int(capacity / qps) + 60

    async def allow(self, bucket_id: str, cost: float | int = 1.0) -> bool:
        if not self.enable:
            return True
        now = time.time()
        key = CacheKeyEnum.TOKEN_BUCKET.format(name=self.name, id=bucket_id)
        state = await self.cache.get(key)
        if not isinstance(state, TokenBucketState):
            state = TokenBucketState(tokens=self.capacity, updated_at=now)

        tokens = min(self.capacity, state.tokens + max(0.0, now - state.updated_at) * self.qps)
        if allowed := tokens >= cost:
            tokens -= cost
        await self.cache.set(key, TokenBucketState(tokens=tokens, updated_at=now), self.expiration)
        return allowed


# 0.5 QPS for a single IP, 3 QPS for global;
# bcrypt run for ~290ms/750ms on 1C1G with light/heavy load
login_ip_limiter = TokenBucketLimiter(**app_config.security.throttle.login_ip.model_dump())
login_global_limiter = TokenBucketLimiter(**app_config.security.throttle.login_global.model_dump())
open_ip_limiter = TokenBucketLimiter(**app_config.security.throttle.open_ip.model_dump())
