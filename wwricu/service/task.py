import asyncio
import traceback
import uuid

from loguru import logger as log

from wwricu.component.task import TaskDef, TaskRegistry
from wwricu.domain.enum import TaskStatusEnum
from wwricu.domain.task import TaskInfoDTO, TaskRunRO, TaskRunVO, TaskSearchRO, TaskStateVO

_running: dict[str, '_TaskRun'] = {}
_last: '_TaskRun | None' = None


class _TaskRun:
    def __init__(self, run_id: str, name: str):
        self.run_id = run_id
        self.name = name
        self.status = TaskStatusEnum.RUNNING
        self.output: str | None = None
        self.error: str | None = None

    def to_vo(self) -> TaskStateVO:
        return TaskStateVO(
            run_id=self.run_id,
            name=self.name,
            status=self.status,
            output=self.output,
            error=self.error,
        )


def search(query: TaskSearchRO) -> list[TaskInfoDTO]:
    return [task_def.to_info() for task_def in TaskRegistry.search(query.keyword)]


async def run(req: TaskRunRO) -> TaskRunVO:
    task_def = TaskRegistry.get(req.name)
    if task_def is None:
        raise ValueError(f'未知任务: {req.name}')
    params = task_def.params_model.model_validate(req.params)
    task_run = _TaskRun(uuid.uuid4().hex, task_def.name)
    _running[task_run.run_id] = task_run
    asyncio.create_task(_execute(task_run, task_def, params))
    return TaskRunVO(run_id=task_run.run_id, name=task_def.name, status=task_run.status)


async def _execute(task_run: _TaskRun, task_def: TaskDef, params):
    global _last
    kwargs = params.model_dump()
    try:
        result = await task_def.func(**kwargs)
        task_run.status = TaskStatusEnum.SUCCESS
        task_run.output = None if result is None else str(result)
    except Exception:
        task_run.status = TaskStatusEnum.FAILED
        task_run.error = traceback.format_exc()
        log.bind(run_id=task_run.run_id, task=task_run.name).error(task_run.error)
    finally:
        _running.pop(task_run.run_id, None)
        _last = task_run


def list_states() -> list[TaskStateVO]:
    states = [task_run.to_vo() for task_run in _running.values()]
    if _last is not None:
        states.append(_last.to_vo())
    return states
