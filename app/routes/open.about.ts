import { apiLoader, methodDenied } from '~/server/http/handler';
import { getConfig } from '~/server/service/manage';
import { sysCache } from '~/server/lib/caches';
import { CacheKey, ConfigKey } from '~/server/domain/enum';
import type { AboutPageVO } from '~/server/domain/types';

// GET /open/about — public about page payload.
// Mirrors api/open.py open_get_about_api (no rate limiter on this route).
export const loader = apiLoader((): AboutPageVO => ({
  content: getConfig(ConfigKey.ABOUT_CONTENT),
  post_count: sysCache.get<number>(CacheKey.POST_COUNT) ?? 0,
  category_count: sysCache.get<number>(CacheKey.CATEGORY_COUNT) ?? 0,
  tag_count: sysCache.get<number>(CacheKey.TAG_COUNT) ?? 0,
  startup_timestamp: sysCache.get<number>(CacheKey.STARTUP_TIMESTAMP) ?? 0,
}));

export const action = methodDenied('GET');
