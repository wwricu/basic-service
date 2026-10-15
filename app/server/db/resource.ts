import { all, localNowString, run } from '~/server/lib/db';
import type { PostResourceRow } from '~/server/domain/types';
import { PostResourceType, type PostResourceTypeEnum } from '~/server/domain/enum';

const TABLE = 'wwr_post_resource';

export function findById(id: number, type: PostResourceTypeEnum | null = null, deleted: boolean = false): PostResourceRow | null {
  let sql = `SELECT * FROM ${TABLE} WHERE deleted = ? AND id = ?`;
  const params: unknown[] = [deleted ? 1 : 0, id];
  if (type !== null) {
    sql += ' AND type = ?';
    params.push(type);
  }
  const rows = all<PostResourceRow>(sql, ...(params as never[]));
  return rows[0] ?? null;
}

// database/resource.py delete_by_keys: UPDATE set deleted=True (onupdate adds update_time).
export function deleteByKeys(keys: string[]): void {
  if (keys.length === 0) return;
  const placeholders = keys.map(() => '?').join(', ');
  run(`UPDATE ${TABLE} SET deleted = 1, update_time = ? WHERE key IN (${placeholders})`, localNowString() as never, ...(keys as never[]));
}

export function findByPostId(postId: number): PostResourceRow[] {
  return all<PostResourceRow>(`SELECT * FROM ${TABLE} WHERE post_id = ? AND deleted = 0`, postId as never);
}

export function findPostsCover(postIds: number[]): Record<number, PostResourceRow> {
  if (postIds.length === 0) return {};
  const placeholders = postIds.map(() => '?').join(', ');
  const rows = all<PostResourceRow & { _post_id: number }>(
    `SELECT r.*, p.id AS _post_id FROM ${TABLE} r ` +
      `JOIN wwr_blog_post p ON r.id = p.cover_id ` +
      `WHERE r.deleted = 0 AND r.type = ? AND p.deleted = 0 AND p.id IN (${placeholders})`,
    PostResourceType.COVER_IMAGE as never,
    ...(postIds as never[]),
  );
  const map: Record<number, PostResourceRow> = {};
  for (const row of rows) {
    const postId = row._post_id;
    delete (row as unknown as Record<string, unknown>)._post_id;
    map[postId] = row;
  }
  return map;
}

export function findDeleted(): PostResourceRow[] {
  return all<PostResourceRow>(`SELECT * FROM ${TABLE} WHERE deleted = 1`);
}

export { TABLE as POST_RESOURCE_TABLE };
