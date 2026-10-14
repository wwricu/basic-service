from typing import Any

from pydantic import Field

from wwricu.domain.common import BaseModel
from wwricu.domain.enum import TaskStatusEnum


class TaskParamVO(BaseModel):
    name: str
    type: str
    required: bool
    default: Any = None


class TaskInfoDTO(BaseModel):
    name: str
    params: list[TaskParamVO] = Field(default_factory=list)


class TaskSearchRO(BaseModel):
    keyword: str = ''


class TaskRunRO(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class TaskRunVO(BaseModel):
    run_id: str
    name: str
    status: TaskStatusEnum


class TaskStateVO(BaseModel):
    """刷新时 GET 返回：运行中的任务 + 最近一次已结束任务。"""
    run_id: str
    name: str
    status: TaskStatusEnum
    output: str | None = None
    error: str | None = None
