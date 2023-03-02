import asyncio
import time


async def sleep(t: int, sign: str | None = ''):
    print(f'before sleep {sign}')
    await asyncio.sleep(t)
    print(f'after sleep {sign}')
    return t


async def test():
    # time: 4s
    tasks = []
    for i in range(5):
        tasks.append(sleep(2, '1'))
    await asyncio.gather(*tasks)
    tasks.clear()
    for i in range(5):
        tasks.append(sleep(2, '2'))
    await asyncio.gather(*tasks)


async def test_await_in_arg():
    tasks = []  # 12s
    for i in range(5):
        tasks.append(sleep(await sleep(2)))
    await asyncio.gather(*tasks)


async def test_await_in_arg2():
    async def await_in_arg():
        await sleep(await sleep(2))

    tasks = []  # 2s
    for i in range(5):
        tasks.append(await_in_arg())
    await asyncio.gather(*tasks)


async def run_with_sync():
    asyncio.create_task(sleep(15))
    print('sync end')


async def main():
    begin = time.time()
    await run_with_sync()
    print(f'time is {int(time.time() - begin)}')
    await asyncio.sleep(20)


if __name__ == '__main__':
    asyncio.run(main())
