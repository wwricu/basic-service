# import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

from config import Config


class AsyncRedis:
    __pool: ConnectionPool = None

    @classmethod
    async def init_redis(cls):
        cls.__pool = ConnectionPool(
            **Config.redis.__dict__,
            decode_responses=True
        )

    @classmethod
    async def get_connection(cls) -> Redis:
        return Redis(connection_pool=cls.__pool)

    @classmethod
    async def test(cls):
        try:
            conn = await cls.get_connection()
            await conn.set('test', '111')
            print('after set')
            print(await conn.get('test'))
        except Exception as e:
            print(e)
