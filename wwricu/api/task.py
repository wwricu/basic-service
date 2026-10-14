from fastapi import APIRouter, Depends

from wwricu.domain.task import TaskInfoDTO, TaskRunRO, TaskRunVO, TaskSearchRO, TaskStateVO
from wwricu.service import security_service, task_service

task_api = APIRouter(prefix='/task', tags=['Task api'], dependencies=[Depends(security_service.require_admin)])


@task_api.post('/search', response_model=list[TaskInfoDTO])
async def search_task_api(query: TaskSearchRO) -> list[TaskInfoDTO]:
    return task_service.search(query)


@task_api.post('/run', response_model=TaskRunVO)
async def run_task_api(req: TaskRunRO) -> TaskRunVO:
    return await task_service.run(req)


@task_api.get('/running', response_model=list[TaskStateVO])
async def running_task_api() -> list[TaskStateVO]:
    return task_service.list_states()
