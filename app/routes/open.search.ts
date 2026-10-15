import { apiLoader, methodDenied } from '~/server/http/handler';
import { openLimiter } from '~/server/service/security';
import { search } from '~/server/service/post';
import { missingIssue, tooLongIssue, tooShortIssue, unprocessable } from '~/server/lib/httpError';

const MIN_KEYWORD = 1;
const MAX_KEYWORD = 128;

// GET /open/post/search?keyword=... — mirrors open_search_posts_api, including
// FastAPI's Query(min_length=1, max_length=128) 422 issue bodies.
export const loader = apiLoader(async (ctx) => {
  await openLimiter(ctx.realIp);
  const keyword = ctx.query('keyword');
  if (keyword === null) throw unprocessable(missingIssue(['query', 'keyword']));
  // Python measures str length in code points, so surrogate pairs count once.
  const length = Array.from(keyword).length;
  if (length < MIN_KEYWORD) throw unprocessable(tooShortIssue(['query', 'keyword'], keyword, MIN_KEYWORD));
  if (length > MAX_KEYWORD) throw unprocessable(tooLongIssue(['query', 'keyword'], keyword, MAX_KEYWORD));
  return search(keyword);
});

export const action = methodDenied('GET');
