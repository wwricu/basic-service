import { all, get, localNowString, run } from '~/server/lib/db';
import { updateSelectiveNotDeleted } from '~/server/db/common';
import { CommonConst } from '~/server/domain/constants';
import { PostStatus, RelationType, TagType, type PostStatusEnum } from '~/server/domain/enum';
import type { BlogPostRow, PostQueryDTO } from '~/server/domain/types';

const POST = 'wwr_blog_post';
const RELATION = 'wwr_entity_relation';
const POST_TAG = 'wwr_post_tag';
const SEARCH = 'wwr_blog_post_search';
export { POST as POST_TABLE, POST_TAG as POST_TAG_TABLE_FOR_JOIN };

export function findById(postId: number): BlogPostRow | null {
  return get<BlogPostRow>(`SELECT * FROM ${POST} WHERE id = ? AND deleted = 0`, postId as never) ?? null;
}

export function findByIdsByTags(tagNames: string[]): number[] {
  if (tagNames.length === 0) return [];
  const placeholders = tagNames.map(() => '?').join(', ');
  const rows = all<{ id: number }>(
    `SELECT p.id FROM ${POST} p ` +
      `JOIN ${RELATION} r ON p.id = r.src_id ` +
      `JOIN ${POST_TAG} t ON t.id = r.dst_id ` +
      `WHERE t.deleted = 0 AND r.deleted = 0 AND p.deleted = 0 AND t.type = ? AND r.type = ? AND t.name IN (${placeholders})`,
    TagType.POST_TAG as never,
    RelationType.POST_TAG as never,
    ...(tagNames as never[]),
  );
  return rows.map((r) => r.id);
}

export function updateSelective(postId: number, values: Record<string, unknown>): void {
  updateSelectiveNotDeleted(POST, postId, values);
}

export function findPublished(postId: number): BlogPostRow | null {
  return (
    get<BlogPostRow>(
      `SELECT * FROM ${POST} WHERE id = ? AND deleted = 0 AND status = ?`,
      postId as never,
      PostStatus.PUBLISHED as never,
    ) ?? null
  );
}

function buildWhere(query: PostQueryDTO): { sql: string; params: unknown[] } {
  const clauses: string[] = [];
  const params: unknown[] = [];
  if (query.status != null) { clauses.push('status = ?'); params.push(query.status); }
  // PostQueryDTO.deleted defaults to False in the pydantic model.
  if (query.deleted !== null) {
    const del = query.deleted ?? false;
    clauses.push('deleted = ?');
    params.push(del ? 1 : 0);
  }
  if (query.category_id != null) { clauses.push('category_id = ?'); params.push(query.category_id); }
  if (query.post_ids != null) {
    clauses.push(`id IN (${query.post_ids.map(() => '?').join(', ')})`);
    params.push(...query.post_ids);
  }
  return { sql: clauses.length ? ` WHERE ${clauses.join(' AND ')}` : '', params };
}

export function findByCriteria(query: PostQueryDTO): BlogPostRow[] {
  const { sql, params } = buildWhere(query);
  let final = `SELECT * FROM ${POST}${sql} ORDER BY create_time DESC`;
  if (query.page_size && query.page_size > 0 && query.page_index && query.page_index > 0) {
    const size = Math.min(query.page_size, 100);
    final += ` LIMIT ${size} OFFSET ${(query.page_index - 1) * size}`;
  }
  return all<BlogPostRow>(final, ...(params as never[]));
}

export function count(query: PostQueryDTO): number {
  const { sql, params } = buildWhere(query);
  const row = get<{ c: number }>(`SELECT COUNT(*) AS c FROM (SELECT 1 FROM ${POST}${sql})`, ...(params as never[]));
  return row ? row.c : 0;
}

// post_db.delete_tags: soft-delete the post's tag relations (update_time stamped by onupdate).
export function deleteTags(postId: number): void {
  run(
    `UPDATE ${RELATION} SET deleted = 1, update_time = ? WHERE type = ? AND deleted = 0 AND src_id = ?`,
    localNowString() as never,
    RelationType.POST_TAG as never,
    postId as never,
  );
}

export function upsertSearchIndex(postId: number, title: string, preview: string, searchContent: string): void {
  run(`DELETE FROM ${SEARCH} WHERE id = ?`, postId as never);
  run(
    `INSERT INTO ${SEARCH} (id, title, preview, search_content) VALUES (?, ?, ?, ?)`,
    postId as never,
    title as never,
    preview as never,
    searchContent as never,
  );
}

export interface SearchRow extends BlogPostRow {
  snippet: string | null;
}

// post_db.search: FTS5 MATCH + bm25 ranking + snippet over the search_content column.
export function search(keyword: string): SearchRow[] {
  if (!keyword || !keyword.trim()) return [];
  const rows = all<SearchRow>(
    `SELECT p.*, snippet(${SEARCH}, 3, '${CommonConst.MARK_BEGIN}', '${CommonConst.MARK_END}', '…', 32) AS snippet ` +
      `FROM ${POST} p JOIN ${SEARCH} s ON p.id = s.id ` +
      `WHERE p.deleted = 0 AND p.status = ? AND ${SEARCH} MATCH ? ` +
      `ORDER BY bm25(${SEARCH}, 10.0, 5.0, 1.0) LIMIT 30`,
    PostStatus.PUBLISHED as never,
    keyword as never,
  );
  for (const p of rows) {
    if (p.snippet && !p.snippet.includes(CommonConst.MARK_BEGIN)) p.snippet = '';
    if (p.snippet) p.snippet = p.snippet.split(CommonConst.TOKEN_SEPARATOR).join('');
  }
  return rows;
}

export type { PostStatusEnum };
