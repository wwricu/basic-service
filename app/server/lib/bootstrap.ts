import { appConfig, config, env, loadAppConfig } from '~/server/lib/config';
import { initStorageClient } from '~/server/lib/storage';
import { initDatabase, closeDatabase } from '~/server/lib/db';
import { initJieba } from '~/server/lib/jieba';
import { LocalCache } from '~/server/lib/cache';
import { sysCache } from '~/server/lib/caches';
import { startScheduler, stopScheduler } from '~/server/lib/scheduler';
import { log } from '~/server/lib/log';
import { CommonConst } from '~/server/domain/constants';
import { CacheKey } from '~/server/domain/enum';
import '~/server/task/demo'; // trigger @task registration (mirrors task/__init__.py import)

// Mirrors the FastAPI lifespan() in service/common.py, plus config.py import-time init.
// RR7 calls bootstrap() once per server process before handling requests.

let bootstrapped = false;

export async function bootstrap(): Promise<void> {
  if (bootstrapped) return; // guard against dev HMR double-instantiation
  bootstrapped = true;

  // config.py: env + init_log() + init_config() at import time.
  appConfig.current = await loadAppConfig();
  initStorageClient();
  log.info(`env=${env.ENV}`);

  // lifespan(): jieba.initialize() -> LocalCache.init() -> scheduler.start()
  initJieba();
  LocalCache.init();
  await initDatabase();
  startScheduler();

  sysCache.set(CacheKey.STARTUP_TIMESTAMP, Math.floor(Date.now() / 1000), 0);

  const sec = config().security;
  log.info(`image qps=${sec.image_ip_qps} open api qps=${sec.open_ip_qps}`);
  log.info(`allow ${sec.login_ip_times} logins in ${sec.login_ip_span} seconds`);
  log.info(`${CommonConst.APP_NAME} startup`);
}

export async function shutdown(): Promise<void> {
  if (!bootstrapped) return;
  bootstrapped = false;
  stopScheduler();
  await closeDatabase();
  await LocalCache.shutdown();
  log.info(`${CommonConst.APP_NAME} Exit`);
}
