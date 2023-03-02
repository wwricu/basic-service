import traceback
from contextvars import ContextVar


ctx_str: ContextVar[str] = ContextVar('ctx_str', default='default')


def depends():
    traceback.print_stack()
    return ctx_str.get()


def test(a: str = depends()):
    print(a, ctx_str.get())
    ctx_str.set('test')


if __name__ == '__main__':
    ctx_str.set('set')
    test()
    print(ctx_str.get())
