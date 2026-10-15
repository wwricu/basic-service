import cron from 'node-cron';
import { backup } from '~/server/lib/db';
import { deleteUnlinkRelation } from '~/server/db/tag';
import { log } from '~/server/lib/log';

// Replaces apscheduler AsyncIOScheduler + CronTrigger in service/common.py lifespan.
// Both jobs are weekly; the exact day/hour only matters as a non-conflicting window.
type CronTask = { stop: () => void };
const tasks: CronTask[] = [];

export function startScheduler(): void {
  // Sunday 03:00 — upload a consistent snapshot of the SQLite file to S3.
  tasks.push(
    cron.schedule('0 3 * * 0', () => {
      void backup().catch((e) => log.error(`Scheduled backup failed: ${String(e)}`));
    }),
  );
  // Sunday 04:00 — drop entity_relation rows pointing at deleted posts/tags.
  tasks.push(
    cron.schedule('0 4 * * 0', () => {
      try {
        deleteUnlinkRelation();
      } catch (e) {
        log.error(`Scheduled relation cleanup failed: ${String(e)}`);
      }
    }),
  );
  log.info('Scheduler started (weekly backup + relation cleanup)');
}

export function stopScheduler(): void {
  for (const t of tasks) t.stop();
  tasks.length = 0;
  log.info('Scheduler stopped');
}
