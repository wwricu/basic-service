import { http } from '~/web/common';
import type { TaskInfoVO, TaskRunRO, TaskRunVO, TaskStateVO } from '~/server/domain/types';

export const searchTaskAPI = async (keyword: string) => {
  return await http.post<TaskInfoVO[]>('/task/search', { keyword });
};

export const runTaskAPI = async (req: TaskRunRO) => {
  return await http.post<TaskRunVO>('/task/run', req);
};

export const runningTaskAPI = async () => {
  return await http.get<TaskStateVO[]>('/task/running');
};
