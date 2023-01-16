# from test.apis import run_apis_all_test
from contextvars import ContextVar


def depends():
    return 2


def test(a: int = depends()):
    print(a)


if __name__ == '__main__':
    test()
    # run_apis_all_test()
