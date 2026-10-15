import { get, run } from '~/server/lib/db';
import type { ConfigKeyEnum } from '~/server/domain/enum';

const TABLE = 'wwr_sys_config';

// database/config.py: upsert = DELETE by key, then INSERT a fresh row.
export function upsert(key: ConfigKeyEnum, value: string): void {
  run(`DELETE FROM ${TABLE} WHERE key = ?`, key as never);
  run(`INSERT INTO ${TABLE} (key, value, deleted) VALUES (?, ?, 0)`, key as never, value as never);
}

// remove: hard DELETE of non-deleted rows for the given keys.
export function remove(keys: ConfigKeyEnum[]): void {
  if (keys.length === 0) return;
  const placeholders = keys.map(() => '?').join(', ');
  run(`DELETE FROM ${TABLE} WHERE key IN (${placeholders}) AND deleted = 0`, ...(keys as never[]));
}

// get: read value straight from DB (no cache), non-deleted only.
export function getConf(key: ConfigKeyEnum): string | null {
  const row = get<{ value: string | null }>(`SELECT value FROM ${TABLE} WHERE key = ? AND deleted = 0`, key as never);
  return row ? row.value : null;
}
