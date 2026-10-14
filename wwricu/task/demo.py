import asyncio

from loguru import logger as log

from wwricu.component.task import task


@task
async def hello(name: str = 'world', times: int = 3) -> str:
    return '\n'.join(f'hello {name} #{i + 1}' for i in range(times))


@task
async def slow_work(seconds: float = 0.3) -> str:
    # 任务自己的过程日志由任务自行处理；阻塞逻辑请自己 await asyncio.to_thread(...)
    log.info('slow_work start')
    await asyncio.sleep(seconds)
    return f'slow work done after {seconds}s'


@task
async def boom() -> None:
    raise RuntimeError('something went wrong')
