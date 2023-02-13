import pickle

from redis.asyncio import ConnectionPool, Redis, StrictRedis

from config import Config, logger


class AsyncRedis:
    __pool: ConnectionPool = None

    @classmethod
    async def init_redis(cls):
        if cls.__pool is None:
            cls.__pool = ConnectionPool(
                **Config.redis.__dict__,
            )
        redis = await cls.get_connection()
        await redis.set('preview_dict', pickle.dumps(dict()))
        await redis.set('count_dict', pickle.dumps(dict()))
        logger.info('redis connected')

    @classmethod
    async def get_connection(cls) -> Redis:
        return StrictRedis(connection_pool=cls.__pool)

    @classmethod
    async def close(cls):
        await cls.__pool.disconnect()
