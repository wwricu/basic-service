import { LocalCache } from '~/server/lib/cache';

// Mirror the named caches instantiated in component/cache.py.
export const sysCache = new LocalCache('sys', 10000, true);
export const queryCache = new LocalCache('query');
export const postCache = new LocalCache('post');
export const postStatusCache = new LocalCache('post_status');
export const imageCache = new LocalCache('image', 10000);
export const bucketCache = new LocalCache('bucket', 100000);
