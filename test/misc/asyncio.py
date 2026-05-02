import asyncio
import time

import pytest



async def sync_func() -> None:
    time.sleep(1)


async def async_func() -> None:
    await asyncio.sleep(1)


async def sync_thread_func() -> None:
    await asyncio.to_thread(time.sleep,1)


async def sync_func_thread(name: str) -> None:
    print(f'sync {name=} cp0')
    await sync_func()
    print(f'sync {name=} cp1')
    await sync_func()
    print(f'sync {name=} cp2')


async def async_func_thread(name: str) -> None:
    print(f'async {name=} cp0')
    await async_func()
    print(f'async {name=} cp1')
    await async_func()
    print(f'async {name=} cp2')


async def sync_func_to_thread(name: str) -> None:
    print(f'thread {name=} cp0')
    await sync_thread_func()
    print(f'thread {name=} cp1')
    await sync_thread_func()
    print(f'thread {name=} cp2')


@pytest.mark.asyncio
async def test_async() -> None:
    await asyncio.gather(
        sync_func_thread('a'),
        sync_func_thread('b'),
        sync_func_thread('c'),
        sync_func_thread('d'),
    )
    print('-----------------')
    await asyncio.gather(
        async_func_thread('a'),
        async_func_thread('b'),
        async_func_thread('c'),
        async_func_thread('d'),
    )
    print('-----------------')
    await asyncio.gather(
        sync_func_to_thread('a'),
        sync_func_to_thread('b'),
        sync_func_to_thread('c'),
        sync_func_to_thread('d'),
    )
