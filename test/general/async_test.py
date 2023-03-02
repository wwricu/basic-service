import asyncio


async def func1():
    print('func1 bef')
    await asyncio.sleep(3)
    print('func1 aft')


async def func2():
    print('func2 bef')
    await asyncio.sleep(3)
    print('func2 aft')


async def func3() -> int:
    print('func3 bef')
    await asyncio.sleep(3)
    print('func3 aft')
    return 1


async def func4(i: int):
    print('func4 bef')
    await asyncio.sleep(3)
    print('func4 aft', i)


async def test():
    tasks = []
    for i in range(5):
        tasks.append(func1())
    await asyncio.gather(*tasks)
    tasks.clear()
    for i in range(5):
        tasks.append(func2())
    await asyncio.gather(*tasks)


async def test_arg():
    tasks = []
    for i in range(5):
        tasks.append(func4(await func3()))
    await asyncio.gather(*tasks)


async def test_arg2():
    async def arg():
        await func4(await func3())

    tasks = []
    for i in range(5):
        tasks.append(arg())
    await asyncio.gather(*tasks)


async def test_append():
    tasks, data = [], []
    for i in range(5):
        tasks.append(data.append(await func3()))
    await asyncio.gather(*tasks)


async def sleep(s: int, label: str | None = None):
    await asyncio.sleep(s)
    print('async end', label)


async def main():
    asyncio.create_task(sleep(5))
    print('sync end')
    await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
