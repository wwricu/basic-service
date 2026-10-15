import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { env, isDebug } from '~/server/lib/config';
import { TimeConst } from '~/server/domain/constants';
import { log } from '~/server/lib/log';

// Mirrors wwricu/component/cache.py LocalCache (LRU + TTL + optional on-disk persistence).
// NOTE: JS single-threaded event loop means all operations here are atomic within a task,
// exactly as the Python comment about "no await inside => no lock needed" implies.

type Expirable = { value: unknown; expire: number }; // expire: epoch seconds, 0 = never

export class LocalCache {
  name: string;
  max_size: number;
  persist: boolean;
  data = new Map<string, Expirable>(); // Map preserves insertion order = LRU
  private static all = new Map<string, LocalCache>();
  private static heartbeat: ReturnType<typeof setInterval> | null = null;

  constructor(name: string, max_size = 10000, persist = false) {
    this.name = name;
    this.max_size = max_size;
    // Python disables persistence under __debug__; mirror that so dev never writes cache files.
    this.persist = persist && !isDebug;
    if (LocalCache.all.has(this.name)) throw new Error(`duplicate cache ${this.name}`);
    LocalCache.all.set(this.name, this);
    if (this.persist) this.load();
  }

  private file() {
    return join(env.LOG_PATH, `${this.name}.cache.json`);
  }

  private load() {
    if (!existsSync(this.file())) return;
    try {
      const raw = JSON.parse(readFileSync(this.file(), 'utf-8')) as [string, Expirable][];
      for (const [k, v] of raw) this.data.set(k, v);
      log.info(`${this.data.size} ${this.name} cache entries loaded`);
    } catch {
      /* ignore corrupt cache */
    }
  }

  private dump() {
    if (!this.persist) return;
    try {
      writeFileSync(this.file(), JSON.stringify([...this.data.entries()]));
      log.info(`${this.data.size} ${this.name} cache entries dumped`);
    } catch (e) {
      log.error(`Failed to dump cache ${this.name} ${String(e)}`);
    }
  }

  get<T = unknown>(key: string | null | undefined): T | null {
    if (typeof key !== 'string') return null;
    const entry = this.data.get(key);
    if (!entry) return null;
    if (entry.expire > 0 && entry.expire <= Date.now() / 1000) {
      this.data.delete(key);
      return null;
    }
    // touch: move to most-recent
    this.data.delete(key);
    this.data.set(key, entry);
    return entry.value as T;
  }

  set(key: string | null | undefined, value: unknown, second: number = TimeConst.CACHE_EXPIRATION): void {
    if (typeof key !== 'string') throw new Error(`bad cache key ${String(key)}`);
    const expire = second > 0 ? Math.floor(Date.now() / 1000) + second : 0;
    this.data.delete(key);
    this.data.set(key, { value, expire });
    if (this.data.size > this.max_size) {
      const oldest = this.data.keys().next().value as string;
      this.data.delete(oldest);
    }
  }

  delete(key: string | null | undefined): void {
    if (typeof key !== 'string') return;
    this.data.delete(key);
  }

  deleteAll(): void {
    this.data.clear();
  }

  close(): void {
    this.dump();
  }

  static init(): void {
    if (LocalCache.heartbeat) return;
    LocalCache.heartbeat = setInterval(() => {
      const now = Date.now() / 1000;
      for (const cache of LocalCache.all.values()) {
        for (const [key, entry] of cache.data) {
          if (entry.expire > 0 && entry.expire <= now) cache.data.delete(key);
        }
      }
    }, 10000);
    LocalCache.heartbeat.unref?.();
  }

  static async shutdown(): Promise<void> {
    if (LocalCache.heartbeat) clearInterval(LocalCache.heartbeat);
    LocalCache.heartbeat = null;
    for (const cache of LocalCache.all.values()) {
      try {
        cache.close();
      } catch (e) {
        log.error(`Failed to close cache ${cache.name} ${String(e)}`);
      }
    }
  }
}
