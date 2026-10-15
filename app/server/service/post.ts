import { randomUUID } from 'node:crypto';
import * as postDb from '~/server/db/post';
import { POST_TABLE } from '~/server/db/post';
import * as tagDb from '~/server/db/tag';
import * as resDb from '~/server/db/resource';
import { POST_RESOURCE_TABLE } from '~/server/db/resource';
import * as commonDb from '~/server/db/common';
import { withTransaction } from '~/server/lib/db';
import { storagePut, storageDelete } from '~/server/lib/storage';
import { config } from '~/server/lib/config';
import { extractImageKeys, extractText } from '~/server/lib/html';
import { tokenize, tokenizeRaw, cutWords, cutJoin } from '~/server/lib/jieba';
import { forbidden, notFound, tooLarge } from '~/server/lib/httpError';
import { toIso } from '~/server/domain/datetime';
import { HttpErrorDetail, TimeConst } from '~/server/domain/constants';
import {
  CacheKey,
  formatKey,
  PostResourceType,
  PostStatus,
  RelationType,
  TagType,
  type PostResourceTypeEnum,
  type PostStatusEnum,
  type TagTypeEnum,
} from '~/server/domain/enum';
import { postStatusCache } from '~/server/lib/caches';
import type {
  BlogPostRow,
  FileUploadVO,
  PageVO,
  PostDetailVO,
  PostPreviewVO,
  PostQueryDTO,
  PostRequestRO,
  PostResourceRow,
  PostSearchVO,
  PostUpdateRO,
  PostTagRow,
  TagUpdateDTO,
  TagVO,
  TrashBinRO,
} from '~/server/domain/types';

// Mirrors wwricu/service/post.py. Every DB operation maps 1:1 onto the ported db layer.

function toTagVO(tag: PostTagRow): TagVO {
  return { id: tag.id, name: tag.name, type: tag.type as TagTypeEnum, count: tag.count ?? null };
}

function toResourceVO(res: PostResourceRow): import('~/server/domain/types').PostResourceVO {
  return { id: res.id, name: res.name, key: res.key, url: res.url ?? '', type: res.type as PostResourceTypeEnum };
}

function setEquals(a: Set<number>, b: Set<number>): boolean {
  if (a.size !== b.size) return false;
  for (const v of a) if (!b.has(v)) return false;
  return true;
}

export function buildQuery(post: PostRequestRO, opts?: { public?: boolean }): PostQueryDTO {
  const isPublic = opts?.public ?? false;
  const query: PostQueryDTO = {
    status: isPublic ? PostStatus.PUBLISHED : post.status ?? null,
    deleted: isPublic ? false : post.deleted ?? false,
    page_size: post.page_size,
    page_index: post.page_index,
    post_ids: post.tag_list ? postDb.findByIdsByTags(post.tag_list) : null,
  };
  if (post.category) {
    const category = tagDb.findCategory(null, post.category);
    if (category) query.category_id = category.id;
  }
  return query;
}

export function listByQuery(query: PostQueryDTO): PageVO<PostPreviewVO> {
  const posts = postDb.findByCriteria(query);
  return {
    page_size: query.page_size ?? null,
    page_index: query.page_index ?? null,
    count: postDb.count(query),
    data: getPreview(posts),
  };
}

export function getDetail(blogPost: BlogPostRow | null): PostDetailVO {
  if (blogPost === null) throw notFound(HttpErrorDetail.POST_NOT_FOUND);
  const category = tagDb.findCategory(blogPost.category_id ?? null);
  const tags = getTags(blogPost);
  const cover = blogPost.cover_id != null ? resDb.findById(blogPost.cover_id, PostResourceType.COVER_IMAGE) : null;

  const detail: PostDetailVO = {
    id: blogPost.id,
    title: blogPost.title,
    cover: cover ? toResourceVO(cover) : null,
    preview: blogPost.preview,
    // `tags` was never populated by the legacy backend, but pydantic still serialised the
    // declared field as null, so the key has to stay on the wire.
    tags: null,
    tag_list: tags.map(toTagVO),
    category: category ? toTagVO(category) : null,
    status: blogPost.status as PostStatusEnum,
    create_time: toIso(blogPost.create_time),
    update_time: toIso(blogPost.update_time),
    content: blogPost.content,
  };
  return detail;
}

export function getPreview(postList: BlogPostRow[]): PostPreviewVO[] {
  const ids = postList.map((p) => p.id);
  const categories = batchGetCategory(postList);
  const tags = tagDb.findTagsByPosts(ids);
  const covers = resDb.findPostsCover(ids);

  return postList.map((post) => {
    const detail: PostPreviewVO = {
      id: post.id,
      title: post.title,
      cover: null,
      preview: post.preview,
      tags: null,
      tag_list: (tags[post.id] ?? []).map(toTagVO),
      category: null,
      status: post.status as PostStatusEnum,
      create_time: toIso(post.create_time),
      update_time: toIso(post.update_time),
    };
    const category = categories[post.id];
    if (category) detail.category = toTagVO(category);
    const cover = covers[post.id];
    if (cover) detail.cover = toResourceVO(cover);
    return detail;
  });
}

export function update(newPost: PostUpdateRO): PostDetailVO {
  return withTransaction(() => {
    const post = postDb.findById(newPost.id);
    if (!post) throw notFound(HttpErrorDetail.POST_NOT_FOUND);

    const resources = resDb.findByPostId(post.id);
    const befKeys = new Set(resources.filter((r) => r.id !== newPost.cover_id).map((r) => r.key));
    const aftKeys = extractImageKeys(newPost.content);
    const deleteKeys = [...befKeys].filter((k) => !aftKeys.has(k));
    if (deleteKeys.length) {
      resDb.deleteByKeys(deleteKeys);
    }

    const tagUpdate: TagUpdateDTO = {
      category_id: newPost.category_id ?? null,
      tag_id_list: newPost.tag_id_list,
      status: newPost.status,
    };
    updateCategory(post, tagUpdate);
    updateTags(post, tagUpdate);

    postDb.updateSelective(newPost.id, {
      title: newPost.title,
      content: newPost.content,
      preview: newPost.preview,
      cover_id: newPost.cover_id ?? null,
      status: newPost.status,
      category_id: newPost.category_id ?? null,
    });
    postDb.upsertSearchIndex(
      newPost.id,
      tokenize(newPost.title),
      tokenize(newPost.preview),
      tokenizeRaw(extractText(newPost.content)),
    );

    return getDetail(postDb.findById(newPost.id));
  });
}

export function updateStatus(postId: number, status: PostStatusEnum): void {
  withTransaction(() => {
    const blogPost = postDb.findById(postId);
    if (!blogPost) throw notFound(HttpErrorDetail.POST_NOT_FOUND);
    const tagUpdate: TagUpdateDTO = {
      category_id: blogPost.category_id ?? null,
      tag_id_list: tagDb.findIdsByPostId(blogPost.id),
      status,
    };
    updateCategory(blogPost, tagUpdate);
    updateTags(blogPost, tagUpdate);
    postDb.updateSelective(blogPost.id, { status: tagUpdate.status });
  });
}

export function updateTags(post: BlogPostRow, tagUpdate: TagUpdateDTO): void {
  const tags = tagDb.findByCriteria({ tag_ids: tagUpdate.tag_id_list, type: TagType.POST_TAG });
  const tagIds = new Set(getTags(post).map((t) => t.id));
  const updateTagIds = new Set(tagUpdate.tag_id_list);

  if (!setEquals(tagIds, updateTagIds)) {
    postDb.deleteTags(post.id);
    const relations = tags.map((t) => ({ src_id: post.id, dst_id: t.id, type: RelationType.POST_TAG }));
    commonDb.insertAll('wwr_entity_relation', 'id', relations);
  }

  const befTagIds = new Set<number>();
  const aftTagIds = new Set<number>();
  if (post.status === PostStatus.PUBLISHED) for (const id of tagIds) befTagIds.add(id);
  if (tagUpdate.status === PostStatus.PUBLISHED) for (const id of updateTagIds) aftTagIds.add(id);
  tagDb.updatePostCount(befTagIds, aftTagIds, TagType.POST_TAG);
}

export function getTags(post: BlogPostRow): PostTagRow[] {
  const ids = tagDb.findIdsByPostId(post.id);
  return tagDb.findByCriteria({ tag_ids: ids, type: TagType.POST_TAG });
}

export function updateCategory(post: BlogPostRow, countUpdate: TagUpdateDTO): void {
  if (post.category_id !== countUpdate.category_id) {
    const category = tagDb.findCategory(countUpdate.category_id ?? null);
    postDb.updateSelective(post.id, { category_id: category?.id ?? null });
  }

  const befCategoryId = new Set<number>();
  const aftCategoryId = new Set<number>();
  if (post.status === PostStatus.PUBLISHED && post.category_id) befCategoryId.add(post.category_id);
  if (countUpdate.status === PostStatus.PUBLISHED && countUpdate.category_id) aftCategoryId.add(countUpdate.category_id);
  tagDb.updatePostCount(befCategoryId, aftCategoryId, TagType.POST_CAT);
}

function batchGetCategory(postList: BlogPostRow[]): Record<number, PostTagRow> {
  const categoryIds = postList.map((p) => p.category_id).filter((x): x is number => x != null);
  if (categoryIds.length === 0) return {};
  const categories = tagDb.findByCriteria({ tag_ids: categoryIds, type: TagType.POST_CAT });
  const dict = new Map(categories.map((c) => [c.id, c]));
  const out: Record<number, PostTagRow> = {};
  for (const post of postList) {
    const tag = post.category_id != null ? dict.get(post.category_id) : undefined;
    if (tag) out[post.id] = tag;
  }
  return out;
}

export interface UploadInput {
  filename: string;
  size: number;
  data: Uint8Array;
}

export async function uploadFile(file: UploadInput, postId: number, fileType: PostResourceTypeEnum): Promise<FileUploadVO> {
  const post = postDb.findById(postId);
  if (!post) throw notFound(HttpErrorDetail.POST_NOT_FOUND);
  if (file.size == null || file.size > config().max_upload_size) throw tooLarge();

  const key = `post/${postId}/${randomUUID().replace(/-/g, '')}`;
  const url = await storagePut(key, file.data);
  const resource = commonDb.insert<PostResourceRow>(POST_RESOURCE_TABLE, 'id', {
    name: file.filename,
    key,
    type: fileType,
    post_id: post.id,
    url,
  });
  return { id: resource.id, name: file.filename, key, location: url };
}

export function processTrash(trashBin: TrashBinRO): void {
  withTransaction(() => {
    if (trashBin.delete) {
      const resources = resDb.findByPostId(trashBin.id);
      resDb.deleteByKeys(resources.map((r) => r.key));
      commonDb.hardDelete(POST_TABLE, trashBin.id);
    } else {
      postDb.updateSelective(trashBin.id, { deleted: false });
    }
  });
}

export async function processResourceTrash(trashBin: TrashBinRO): Promise<void> {
  if (trashBin.delete === false) throw forbidden();
  const resource = resDb.findById(trashBin.id, null, true);
  commonDb.hardDelete(POST_RESOURCE_TABLE, trashBin.id);
  if (resource) {
    await storageDelete(resource.key);
  }
}

export function getStatus(postId: number): PostStatusEnum {
  const cacheKey = formatKey(CacheKey.POST, { id: postId });
  const cached = postStatusCache.get<PostStatusEnum>(cacheKey);
  if (cached) return cached;
  const post = postDb.findById(postId);
  if (!post) throw notFound();
  const status = post.status as PostStatusEnum;
  postStatusCache.set(cacheKey, status, TimeConst.ONE_DAY_SECONDS);
  return status;
}

export function search(keyword: string): PostSearchVO[] {
  if (!keyword || !keyword.trim()) return [];
  const cleaned = keyword.replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, ' ').trim();
  const words = cutWords(cleaned);
  if (words.length === 0) return [];
  const query = cutJoin(words.join(' OR '));

  const rows = postDb.search(query);
  const details = getPreview(rows);
  return rows.map((row, i) => ({ ...details[i], snippet: row.snippet ?? null }));
}
