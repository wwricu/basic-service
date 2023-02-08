# import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

from config import Config


class AsyncRedis:
    __pool: ConnectionPool = None

    @classmethod
    async def init_redis(cls):
        cls.__pool = ConnectionPool(
            **Config.redis.__dict__,
        )

    @classmethod
    async def get_connection(cls) -> Redis:
        return Redis(connection_pool=cls.__pool)
