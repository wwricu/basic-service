import { all, get, localNowString, run, withTransaction } from '~/server/lib/db';
import { PostStatus } from '~/server/domain/enum';

// Generic helpers mirroring wwricu/database/common.py plus the ORM onupdate behaviour
// (every UPDATE also sets update_time; every INSERT leaves create_time/update_time to DB defaults).

type Row = Record<string, unknown>;

// wwricu/domain/entity.py fills several columns in on the Python side (`default=`, not a DDL
// DEFAULT): Base.deleted for every table plus BlogPost/PostTag's own. Those columns are NOT NULL
// in SQLite, so an INSERT that omits one has to apply the same value the ORM would have —
// otherwise creating a tag or a new draft post aborts on the NOT NULL constraint.
const ENTITY_DEFAULTS: Record<string, Row> = {
  wwr_blog_post: { deleted: false, title: '', content: '', preview: '', status: PostStatus.DRAFT },
  wwr_post_tag: { deleted: false, count: 0 },
  wwr_entity_relation: { deleted: false },
  wwr_post_resource: { deleted: false },
  wwr_sys_config: { deleted: false },
};

function buildInsert(table: string, data: Row): { sql: string; values: unknown[] } {
  const provided: Row = {};
  for (const [col, value] of Object.entries(data)) {
    if (value !== undefined) provided[col] = value;
  }
  const merged: Row = { ...(ENTITY_DEFAULTS[table] ?? {}), ...provided };
  const cols = Object.keys(merged);
  const placeholders = cols.map(() => '?').join(', ');
  return {
    sql: `INSERT INTO ${table} (${cols.join(', ')}) VALUES (${placeholders})`,
    values: cols.map((c) => normalize(merged[c])),
  };
}

// Insert a full entity and return the persisted row (mirrors common_db.insert + s.refresh).
export function insert<T = Row>(table: string, idColumn: string, data: Row): T {
  const { sql, values } = buildInsert(table, data);
  const res = run(sql, ...(values as never[]));
  const id = data.id !== undefined ? (data.id as number) : Number(res.lastInsertRowid);
  return get<T>(`SELECT * FROM ${table} WHERE ${idColumn} = ?`, id as never) as T;
}

export function insertAll<T = Row>(table: string, idColumn: string, rows: Row[]): T[] {
  return withTransaction(() => rows.map((r) => insert<T>(table, idColumn, r)));
}

export function hardDelete(table: string, primaryId: number): void {
  // Python: DELETE ... WHERE id == primary_id AND deleted == True
  run(`DELETE FROM ${table} WHERE id = ? AND deleted = 1`, primaryId as never);
}

export function recover(table: string, primaryId: number): void {
  // Python: UPDATE ... SET deleted=False WHERE id == primary_id AND deleted == True (onupdate adds update_time)
  run(
    `UPDATE ${table} SET deleted = 0, update_time = ? WHERE id = ? AND deleted = 1`,
    localNowString() as never,
    primaryId as never,
  );
}

// Apply an arbitrary selective update, always stamping update_time (SQLAlchemy onupdate semantics).
export function updateSelective(table: string, primaryId: number, values: Row): void {
  const cols = Object.keys(values).filter((c) => values[c] !== undefined);
  const setSql = [...cols.map((c) => `${c} = ?`), 'update_time = ?'].join(', ');
  const params = [...cols.map((c) => normalize(values[c])), localNowString()];
  run(`UPDATE ${table} SET ${setSql} WHERE id = ?`, ...(params as never[]), primaryId as never);
}

// updateSelective used by tag/post that also constrain deleted == False.
export function updateSelectiveNotDeleted(table: string, primaryId: number, values: Row): void {
  const cols = Object.keys(values).filter((c) => values[c] !== undefined);
  const setSql = [...cols.map((c) => `${c} = ?`), 'update_time = ?'].join(', ');
  const params = [...cols.map((c) => normalize(values[c])), localNowString()];
  run(`UPDATE ${table} SET ${setSql} WHERE id = ? AND deleted = 0`, ...(params as never[]), primaryId as never);
}

// Booleans must be stored as 0/1 for SQLite (SQLAlchemy does the same for Boolean columns).
export function normalize(v: unknown): unknown {
  if (typeof v === 'boolean') return v ? 1 : 0;
  return v;
}

export function rowsFrom<T extends Row = Row>(sql: string, params: unknown[] = []): T[] {
  return all<T>(sql, ...(params as never[]));
}
