import asyncio
import os

from anyio import Path


async def test():
    path = Path('./test/path_test.py')
    print(path.suffix)
    print(path.name)
    print(await path.absolute())
    print(path.__fspath__())
    print('end')
    print(os.listdir('.'))


async def join(path: Path):
    return path.joinpath('test3/test4')


async def main():
    path = Path('test/test2')
    print((await join(path)).__fspath__())
    print(path.__fspath__())

if __name__ == '__main__':
    asyncio.run(main())
