import { apiAction, methodDenied } from '~/server/http/handler';
import { openLimiter } from '~/server/service/security';
import { buildQuery, listByQuery } from '~/server/service/post';
import { queryCache } from '~/server/lib/caches';
import { parsePostRequestRO, readJsonObject } from '~/server/domain/validate';
import { CacheKey, formatKey } from '~/server/domain/enum';
import type { PostRequestRO } from '~/server/domain/types';

// POST /open/post/all — published posts page for the public blog.
// Mirrors api/open.py open_get_posts_api (query cache + open rate limiter).
function allPostsKey(req: PostRequestRO): string {
  const tagList = req.tag_list && req.tag_list.length ? [...req.tag_list].sort().join(',') : '';
  return formatKey(CacheKey.ALL_POSTS, {
    page_index: req.page_index,
    page_size: req.page_size,
    category: req.category ?? '',
    tag_list: tagList,
  });
}

export const action = apiAction(async (ctx) => {
  // FastAPI solves the rate-limit dependency before validating the body.
  await openLimiter(ctx.realIp);
  const req = parsePostRequestRO(await readJsonObject(ctx.request));

  const cacheKey = allPostsKey(req);
  const cached = queryCache.get(cacheKey);
  if (cached) return cached;

  const response = listByQuery(buildQuery(req, { public: true }));
  queryCache.set(cacheKey, response);
  return response;
});

export const loader = methodDenied('POST');
