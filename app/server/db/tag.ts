import { all, get, localNowString, run } from '~/server/lib/db';
import { updateSelectiveNotDeleted } from '~/server/db/common';
import { RelationType, TagType, type TagTypeEnum } from '~/server/domain/enum';
import type { PostTagRow, TagQueryDTO } from '~/server/domain/types';

const POST_TAG = 'wwr_post_tag';
const RELATION = 'wwr_entity_relation';
const POST = 'wwr_blog_post';
export { POST_TAG as POST_TAG_TABLE };

function buildWhere(query: TagQueryDTO): { sql: string; params: unknown[] } {
  const clauses: string[] = [];
  const params: unknown[] = [];
  if (query.type != null) { clauses.push('type = ?'); params.push(query.type); }
  // TagQueryDTO.deleted defaults to False in the pydantic model: absent -> non-deleted only,
  // an explicit null is the only way to query across both states.
  if (query.deleted !== null) {
    const del = query.deleted ?? false;
    clauses.push('deleted = ?');
    params.push(del ? 1 : 0);
  }
  if (query.tag_ids != null) {
    clauses.push(`id IN (${query.tag_ids.map(() => '?').join(', ')})`);
    params.push(...query.tag_ids);
  }
  if (query.name != null) { clauses.push('name = ?'); params.push(query.name); }
  return { sql: clauses.length ? ` WHERE ${clauses.join(' AND ')}` : '', params };
}

export function findByCriteria(query: TagQueryDTO): PostTagRow[] {
  const { sql, params } = buildWhere(query);
  let final = `SELECT * FROM ${POST_TAG}${sql} ORDER BY create_time DESC`;
  if (query.page_size && query.page_size > 0 && query.page_index && query.page_index > 0) {
    const size = Math.min(query.page_size, 100);
    final += ` LIMIT ${size} OFFSET ${(query.page_index - 1) * size}`;
  }
  return all<PostTagRow>(final, ...(params as never[]));
}

export function count(query: TagQueryDTO): number {
  const { sql, params } = buildWhere(query);
  const row = get<{ c: number }>(`SELECT COUNT(*) AS c FROM (SELECT 1 FROM ${POST_TAG}${sql})`, ...(params as never[]));
  return row ? row.c : 0;
}

// database/tag.py update_post_count: CASE decrement removed, increment added, else unchanged.
export function updatePostCount(befTagIds: Set<number>, aftTagIds: Set<number>, tagType: TagTypeEnum): void {
  if (setEquals(befTagIds, aftTagIds)) return;
  const unionIds = [...new Set([...befTagIds, ...aftTagIds])];
  if (unionIds.length === 0) return;
  const removed = [...befTagIds].filter((x) => !aftTagIds.has(x));
  const added = [...aftTagIds].filter((x) => !befTagIds.has(x));

  const conds: string[] = [];
  const orderedParams: unknown[] = [];
  if (removed.length) {
    conds.push(`WHEN id IN (${removed.map(() => '?').join(', ')}) THEN count - 1`);
    orderedParams.push(...removed);
  }
  if (added.length) {
    conds.push(`WHEN id IN (${added.map(() => '?').join(', ')}) THEN count + 1`);
    orderedParams.push(...added);
  }
  const caseExpr = conds.length ? `CASE ${conds.join(' ')} ELSE count END` : 'count';
  const placeholders = unionIds.map(() => '?').join(', ');

  run(
    `UPDATE ${POST_TAG} SET count = ${caseExpr}, update_time = ? WHERE type = ? AND id IN (${placeholders})`,
    ...(orderedParams as never[]),
    localNowString() as never,
    tagType as never,
    ...(unionIds as never[]),
  );
}

export function findTagsByPosts(postIds: number[]): Record<number, PostTagRow[]> {
  if (postIds.length === 0) return {};
  const placeholders = postIds.map(() => '?').join(', ');
  const rows = all<PostTagRow & { _src_id: number }>(
    `SELECT t.*, r.src_id AS _src_id FROM ${POST_TAG} t ` +
      `JOIN ${RELATION} r ON t.id = r.dst_id ` +
      `WHERE t.deleted = 0 AND t.type = ? AND r.type = ? AND r.deleted = 0 AND r.src_id IN (${placeholders})`,
    TagType.POST_TAG as never,
    RelationType.POST_TAG as never,
    ...(postIds as never[]),
  );
  const map: Record<number, PostTagRow[]> = {};
  for (const row of rows) {
    const postId = row._src_id;
    delete (row as unknown as Record<string, unknown>)._src_id;
    (map[postId] ||= []).push(row);
  }
  return map;
}

export function updateSelective(tagId: number, values: Record<string, unknown>): void {
  updateSelectiveNotDeleted(POST_TAG, tagId, values);
}

export function findIdsByPostId(postId: number): number[] {
  const rows = all<{ dst_id: number }>(
    `SELECT dst_id FROM ${RELATION} WHERE type = ? AND deleted = 0 AND src_id = ?`,
    RelationType.POST_TAG as never,
    postId as never,
  );
  return rows.map((r) => r.dst_id);
}

export function deleteUnlinkRelation(): void {
  run(
    `DELETE FROM ${RELATION} ` +
      `WHERE NOT EXISTS (SELECT 1 FROM ${POST} b WHERE b.id = ${RELATION}.src_id) ` +
      `OR NOT EXISTS (SELECT 1 FROM ${POST_TAG} t WHERE t.id = ${RELATION}.dst_id)`,
  );
}

export function findCategory(categoryId: number | null = null, name: string | null = null): PostTagRow | null {
  if (categoryId == null && name == null) return null;
  const query: TagQueryDTO = { type: TagType.POST_CAT };
  if (categoryId != null) query.tag_ids = [categoryId];
  if (name != null) query.name = name;
  const tags = findByCriteria(query);
  if (tags.length > 1) throw new Error('multiple categories matched');
  return tags[0] ?? null;
}

function setEquals(a: Set<number>, b: Set<number>): boolean {
  if (a.size !== b.size) return false;
  for (const v of a) if (!b.has(v)) return false;
  return true;
}
