import asyncio
import uuid

import pytest

from wwricu.component.token_bucket import TokenBucketLimiter


@pytest.mark.asyncio
async def test_token_bucket_refill():
    limiter = TokenBucketLimiter(name='test', capacity=5, qps=10.0)
    ip = uuid.uuid4().hex[:8]
    for _ in range(5):
        assert await limiter.allow(ip)
    assert not await limiter.allow(ip)
    await asyncio.sleep(0.2)
    assert await limiter.allow(ip)


@pytest.mark.asyncio
async def test_throttle_concurrent():
    from wwricu.service.security import throttle
    call_count = 0

    @throttle(concurrent=1, timeout=0.05)
    async def slow_task():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.2)

    await slow_task()
    assert call_count == 1

    results = await asyncio.gather(slow_task(), slow_task(), return_exceptions=True)
    successes = [r for r in results if not isinstance(r, Exception)]
    throttled = [r for r in results if isinstance(r, Exception)]
    assert len(successes) >= 1
    assert len(throttled) >= 1
