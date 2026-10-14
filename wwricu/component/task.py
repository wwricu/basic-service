import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger as log
from pydantic import BaseModel as PydanticBaseModel, ConfigDict

from wwricu.domain.task import TaskInfoDTO, TaskParamVO


class TaskDef:
    def __init__(self, name: str, func: Callable, params_model: type[PydanticBaseModel]):
        self.name = name
        self.func = func
        self.params_model = params_model

    def to_info(self) -> TaskInfoDTO:
        schema = self.params_model.model_json_schema()
        props: dict[str, Any] = schema.get('properties', {})
        required: set[str] = set(schema.get('required', []))
        return TaskInfoDTO(
            name=self.name,
            params=[
                TaskParamVO(
                    name=key,
                    type=_resolve_type(prop),
                    required=key in required,
                    default=prop.get('default'),
                )
                for key, prop in props.items()
            ],
        )


class TaskRegistry:
    _tasks: dict[str, TaskDef] = {}

    @classmethod
    def register(cls, task_def: TaskDef):
        if task_def.name in cls._tasks:
            raise ValueError(f'duplicate task name: {task_def.name}')
        cls._tasks[task_def.name] = task_def
        log.info(f'task registered: {task_def.name}')

    @classmethod
    def get(cls, name: str) -> TaskDef | None:
        return cls._tasks.get(name)

    @classmethod
    def all(cls) -> list[TaskDef]:
        return list(cls._tasks.values())

    @classmethod
    def search(cls, keyword: str) -> list[TaskDef]:
        kw = keyword.strip().lower()
        if not kw:
            return cls.all()
        return [task_def for task_def in cls._tasks.values() if kw in task_def.name.lower()]


def task(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """把 async 函数注册为任务，任务名即函数名（不支持别名，重名报错）。

    任务必须是 async def，由返回值类型 Callable[..., Awaitable[...]] 约束：
    传入非 async 函数会在 mypy 静态检查报错；若绕过类型，运行时 await 也会自然失败。
    参数直接来自函数签名（类型注解 + 默认值），自动导出给前端渲染输入表单。
    任务的输出由任务自己处理（自行 log 或 return），框架不拦截 stdout。
    """
    TaskRegistry.register(TaskDef(func.__name__, func, _infer_model(func)))
    return func


def _infer_model(func: Callable) -> type[PydanticBaseModel]:
    annotations: dict[str, Any] = {}
    namespace: dict[str, Any] = {}
    for param in inspect.signature(func).parameters.values():
        ann = param.annotation if param.annotation is not inspect._empty else Any
        annotations[param.name] = ann
        if param.default is not inspect._empty:
            namespace[param.name] = param.default
    namespace['__annotations__'] = annotations
    namespace['__model_config__'] = ConfigDict(arbitrary_types_allowed=True)
    return type(f'{func.__name__}Params', (PydanticBaseModel,), namespace)


def _resolve_type(prop: dict[str, Any]) -> str:
    if (t := prop.get('type')) and t != 'null':
        return t
    for option in prop.get('anyOf', []):
        if (t := option.get('type')) and t != 'null':
            return t
    return 'string'
