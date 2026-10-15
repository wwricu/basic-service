import { log } from '~/server/lib/log';
import type { TaskInfoDTO, TaskParamVO } from '~/server/domain/types';

// Mirrors wwricu/component/task.py: a registry of named async tasks whose parameter schema
// is exported to the admin UI so it can render an input form. Python inferred the pydantic
// model from the function signature via @task; in TS the schema is declared explicitly.

export type TaskFn = (args: Record<string, unknown>) => Promise<unknown>;

export interface TaskDef {
  name: string;
  func: TaskFn;
  params: TaskParamVO[];
}

class TaskRegistry {
  private static tasks = new Map<string, TaskDef>();

  static register(def: TaskDef): void {
    if (this.tasks.has(def.name)) throw new Error(`duplicate task name: ${def.name}`);
    this.tasks.set(def.name, def);
    log.info(`task registered: ${def.name}`);
  }

  static get(name: string): TaskDef | undefined {
    return this.tasks.get(name);
  }

  static all(): TaskDef[] {
    return [...this.tasks.values()];
  }

  static search(keyword: string): TaskDef[] {
    const kw = keyword.trim().toLowerCase();
    if (!kw) return this.all();
    return this.all().filter((t) => t.name.toLowerCase().includes(kw));
  }
}

// Convenience registrar used by task modules at import time.
export function task(name: string, params: TaskParamVO[], func: TaskFn): void {
  TaskRegistry.register({ name, params, func });
}

export { TaskRegistry };

// Coerce + validate raw params against the declared schema (mirrors params_model.model_validate):
// fill defaults, cast numeric/boolean inputs, keep unknown keys out.
export function coerceParams(def: TaskDef, raw: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const p of def.params) {
    const v = raw?.[p.name];
    if (v === undefined || v === null) {
      if (p.required) throw new Error(`missing required param: ${p.name}`);
      out[p.name] = p.default ?? null;
      continue;
    }
    out[p.name] = castParam(v, p.type);
  }
  return out;
}

function castParam(v: unknown, type: string): unknown {
  switch (type) {
    case 'number':
      return typeof v === 'number' ? v : Number(v);
    case 'integer':
      return Math.round(typeof v === 'number' ? v : Number(v));
    case 'boolean':
      return typeof v === 'boolean' ? v : Boolean(v);
    case 'string':
      return String(v);
    default:
      return v;
  }
}

export function toInfo(def: TaskDef): TaskInfoDTO {
  return { name: def.name, params: def.params };
}
