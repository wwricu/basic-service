import { apiLoader, methodDenied } from '~/server/http/handler';
import { findByCriteria } from '~/server/db/tag';
import { queryCache } from '~/server/lib/caches';
import { enumIssue, unprocessable } from '~/server/lib/httpError';
import { CacheKey, TagType, formatKey, type TagTypeEnum } from '~/server/domain/enum';
import type { TagVO } from '~/server/domain/types';

// GET /open/tags/:tagType — public tag/category list, query-cache backed.
// Mirrors api/open.py open_get_tags_api. tagType is a TagTypeEnum path param, so an
// unknown value is the same pydantic enum issue FastAPI returned (422, not 400).
export const loader = apiLoader(async (ctx) => {
  const raw = ctx.params.tagType;
  if (raw !== TagType.POST_TAG && raw !== TagType.POST_CAT) {
    throw unprocessable(enumIssue(['path', 'tag_type'], raw, Object.values(TagType)));
  }
  const tagType = raw as TagTypeEnum;

  const cacheKey = formatKey(CacheKey.ALL_TAGS, { type: tagType });
  const cached = queryCache.get<TagVO[]>(cacheKey);
  if (cached) return cached;

  const response = findByCriteria({ type: tagType }).map((tag) => ({
    id: tag.id,
    name: tag.name,
    type: tag.type as TagTypeEnum,
    count: tag.count ?? null,
  }));
  queryCache.set(cacheKey, response);
  return response;
});

export const action = methodDenied('GET');
