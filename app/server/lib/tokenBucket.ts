import { bucketCache } from '~/server/lib/caches';
import { config } from '~/server/lib/config';
import { CacheKey, formatKey } from '~/server/domain/enum';
import type { TokenBucketState } from '~/server/domain/types';

// Mirrors wwricu/component/token_bucket.py.
class TokenBucket {
  private capacity: number;
  private speed: number;
  private expiration: number;

  constructor(public name: string, speed: number, capacity: number) {
    if (capacity <= 0 || speed <= 0) throw new Error('invalid token bucket');
    this.speed = speed;
    this.capacity = capacity;
    this.expiration = Math.max(Math.floor(capacity / speed), 60);
  }

  async allow(bucketId: string, qps: number = 1.0): Promise<boolean> {
    if (!qps) return true;
    return this.cost(bucketId, this.speed / qps);
  }

  cost(bucketId: string, cost: number): boolean {
    const now = Date.now() / 1000;
    const key = formatKey(CacheKey.TOKEN_BUCKET, { name: this.name, id: bucketId });
    let state = bucketCache.get<TokenBucketState>(key);
    if (!state) state = { tokens: this.capacity, updated_at: now };

    const tokens = Math.min(this.capacity, state.tokens + Math.max(0, now - state.updated_at) * this.speed);
    const allowed = tokens >= cost;
    const next: TokenBucketState = { tokens: allowed ? tokens - cost : tokens, updated_at: now };
    bucketCache.set(key, next, this.expiration);
    return allowed;
  }

  reset(bucketId: string): void {
    bucketCache.delete(formatKey(CacheKey.TOKEN_BUCKET, { name: this.name, id: bucketId }));
  }
}

export const defaultBucket = new TokenBucket('default', 100.0, 150.0);

// login bucket is configured from security at first use (config may load after module import).
let _loginBucket: TokenBucket | null = null;
export function loginBucket(): TokenBucket {
  if (!_loginBucket) {
    _loginBucket = new TokenBucket('login', 1.0, config().security.login_ip_span);
  }
  return _loginBucket;
}
