import { randomUUID } from 'node:crypto';
import { TaskRegistry, coerceParams, toInfo } from '~/server/lib/taskRegistry';
import { log } from '~/server/lib/log';
import { badRequest } from '~/server/lib/httpError';
import { TaskStatus } from '~/server/domain/enum';
import type { TaskInfoDTO, TaskRunRO, TaskRunVO, TaskSearchRO, TaskStateVO } from '~/server/domain/types';

// Mirrors wwricu/service/task.py: fire-and-forget execution tracked in memory, with the
// most recent finished run kept so the admin UI can still show its result after completion.

interface TaskRun {
  runId: string;
  name: string;
  status: (typeof TaskStatus)[keyof typeof TaskStatus];
  output: string | null;
  error: string | null;
}

const running = new Map<string, TaskRun>();
let last: TaskRun | null = null;

function toVO(run: TaskRun): TaskStateVO {
  return { run_id: run.runId, name: run.name, status: run.status, output: run.output, error: run.error };
}

export function search(query: TaskSearchRO): TaskInfoDTO[] {
  return TaskRegistry.search(query.keyword ?? '').map(toInfo);
}

export function run(req: TaskRunRO): TaskRunVO {
  const def = TaskRegistry.get(req.name);
  if (!def) throw badRequest(`未知任务: ${req.name}`);
  const params = coerceParams(def, req.params ?? {});
  const taskRun: TaskRun = { runId: randomUUID().replace(/-/g, ''), name: def.name, status: TaskStatus.RUNNING, output: null, error: null };
  running.set(taskRun.runId, taskRun);
  void execute(taskRun, def.name, params);
  return { run_id: taskRun.runId, name: def.name, status: taskRun.status };
}

async function execute(taskRun: TaskRun, name: string, params: Record<string, unknown>): Promise<void> {
  const def = TaskRegistry.get(name);
  if (!def) return;
  try {
    const result = await def.func(params);
    taskRun.status = TaskStatus.SUCCESS;
    taskRun.output = result === null || result === undefined ? null : String(result);
  } catch (e) {
    taskRun.status = TaskStatus.FAILED;
    taskRun.error = e instanceof Error ? (e.stack ?? e.message) : String(e);
    log.error(`task ${name} run ${taskRun.runId} failed: ${taskRun.error}`);
  } finally {
    running.delete(taskRun.runId);
    last = taskRun;
  }
}

export function listStates(): TaskStateVO[] {
  const states = [...running.values()].map(toVO);
  if (last) states.push(toVO(last));
  return states;
}
