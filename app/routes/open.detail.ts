import { apiLoader, methodDenied } from '~/server/http/handler';
import { getDetail } from '~/server/service/post';
import { findPublished } from '~/server/db/post';
import { postCache } from '~/server/lib/caches';
import { intIssue, notFound, unprocessable } from '~/server/lib/httpError';
import { HttpErrorDetail } from '~/server/domain/constants';
import { CacheKey, formatKey } from '~/server/domain/enum';

// GET /open/post/detail/:postId — public post detail (published only), post_cache backed.
// Mirrors api/open.py open_get_post_api: post_id is an int path param, so garbage ids are
// the same 422 int_parsing issue FastAPI produced before the lookup ever ran.
export const loader = apiLoader(async (ctx) => {
  const raw = ctx.params.postId;
  if (!/^[-+]?\d+$/.test(raw)) throw unprocessable(intIssue(['path', 'post_id'], raw));
  const postId = Number(raw);
  const cacheKey = formatKey(CacheKey.POST, { id: postId });

  const cached = postCache.get<import('~/server/domain/types').BlogPostRow>(cacheKey);
  if (cached) return getDetail(cached);

  const post = findPublished(postId);
  if (!post) throw notFound(HttpErrorDetail.POST_NOT_FOUND);
  postCache.set(cacheKey, post);
  return getDetail(post);
});

export const action = methodDenied('GET');
