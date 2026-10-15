import { existsSync, readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { config } from '~/server/lib/config';
import { log } from '~/server/lib/log';

// Single shared connection, mirroring the one-database-per-process model.
let db: DatabaseSync | null = null;

// Storage + DB are interdependent (database bootstrap may pull the file from storage, and
// backup pushes it back). Use lazy require inside functions to avoid a static import cycle,
// exactly like the Python component/database <-> component/storage relationship.
function storage(): typeof import('~/server/lib/storage') {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require('~/server/lib/storage');
}
export function localNowString(): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).formatToParts(new Date());
  const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}

export async function initDatabase(): Promise<void> {
  const file = config().database.database;
  if (!existsSync(file)) {
    if (await storage().storageEnsureFile(file)) {
      log.info(`Downloaded database as ${file}`);
    }
  }
  db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode=WAL');
}

export function getDb(): DatabaseSync {
  if (!db) throw new Error('database not initialised');
  return db;
}

// node:sqlite binds null/number/bigint/string/Uint8Array. Booleans are normalized to 0/1
// at the db layer (see db/common.normalize), so they are intentionally not a bindable type.
export type SqlParam = string | number | bigint | null | Uint8Array;

export function all<T = Record<string, unknown>>(sql: string, ...params: SqlParam[]): T[] {
  return getDb().prepare(sql).all(...params) as T[];
}

export function get<T = Record<string, unknown>>(sql: string, ...params: SqlParam[]): T | undefined {
  return getDb().prepare(sql).get(...params) as T | undefined;
}

export function run(sql: string, ...params: SqlParam[]): { changes: number | bigint; lastInsertRowid: number | bigint } {
  return getDb().prepare(sql).run(...params);
}

export function execSql(sql: string): void {
  getDb().exec(sql);
}

// Synchronous transaction with savepoint-based nesting, matching the ORM nested-session reuse.
let depth = 0;
export function withTransaction<T>(fn: () => T): T {
  const d = getDb();
  if (depth === 0) {
    d.exec('BEGIN IMMEDIATE');
    depth = 1;
    try {
      const r = fn();
      d.exec('COMMIT');
      return r;
    } catch (e) {
      try { d.exec('ROLLBACK'); } catch { /* ignore */ }
      throw e;
    } finally {
      depth = 0;
    }
  }
  const sp = `sp_${depth}`;
  d.exec(`SAVEPOINT ${sp}`);
  depth += 1;
  try {
    const r = fn();
    d.exec(`RELEASE ${sp}`);
    return r;
  } catch (e) {
    d.exec(`ROLLBACK TO ${sp}`);
    d.exec(`RELEASE ${sp}`);
    throw e;
  } finally {
    depth -= 1;
  }
}

// ---- DatabaseManager.backup / restore / close (component/database.py) ----

export async function backup(): Promise<void> {
  // Python skips backup while in debug (__debug__) and when the file is absent.
  if (process.env.ENV !== 'prod') return;
  const file = config().database.database;
  if (!db || !existsSync(file)) return;
  log.info(`Backup database ${file}`);
  // Fold the WAL into the main file so a plain read yields a consistent snapshot.
  db.exec('PRAGMA wal_checkpoint(TRUNCATE)');
  try {
    const data = readFileSync(file);
    await storage().storagePut(file, data);
    log.info('Backup database success');
  } catch (e) {
    log.error(`Backup failed: ${String(e)}`);
    throw e;
  }
}

export function restore(): void {
  const file = config().database.database;
  if (db) db.close();
  db = null;
  if (existsSync(file)) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { rmSync } = require('node:fs') as typeof import('node:fs');
    rmSync(file);
  }
  initDatabase();
  log.info('Restore database success');
}

export async function closeDatabase(): Promise<void> {
  await backup();
}
