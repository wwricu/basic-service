import { imageCache, postCache, queryCache, sysCache } from '~/server/lib/caches';
import { storagePresignUrl } from '~/server/lib/storage';
import * as postDb from '~/server/db/post';
import * as tagDb from '~/server/db/tag';
import { TimeConst } from '~/server/domain/constants';
import { CacheKey, PostStatus, TagType } from '~/server/domain/enum';
import { log } from '~/server/lib/log';

// Mirrors wwricu/service/common.py.

// FastAPI dependency used as a post-handler hook (code after `yield`): refresh the cached
// global counts after a mutation. Route handlers call it after the service action.
export async function resetSysConfig(): Promise<void> {
  const postCount = postDb.count({ status: PostStatus.PUBLISHED, deleted: false });
  const categoryCount = tagDb.count({ type: TagType.POST_CAT });
  const tagCount = tagDb.count({ type: TagType.POST_TAG });
  log.info(`post_count=${postCount} category_count=${categoryCount} tag_count=${tagCount}`);
  sysCache.set(CacheKey.POST_COUNT, postCount, 0);
  sysCache.set(CacheKey.CATEGORY_COUNT, categoryCount, 0);
  sysCache.set(CacheKey.TAG_COUNT, tagCount, 0);
}

// Presigned image URL with a 1-day cache, mirroring get_image_url().
export async function getImageUrl(key: string): Promise<string> {
  const cached = imageCache.get<string>(key);
  if (cached) return cached;
  const url = await storagePresignUrl(key, 2 * TimeConst.ONE_DAY_SECONDS);
  imageCache.set(key, url, TimeConst.ONE_DAY_SECONDS);
  return url;
}

export { postCache, queryCache, sysCache };
