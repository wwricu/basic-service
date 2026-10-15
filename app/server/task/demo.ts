import { task } from '~/server/lib/taskRegistry';
import { log } from '~/server/lib/log';

// Mirrors wwricu/task/demo.py — importing this module registers the sample tasks.

task(
  'hello',
  [
    { name: 'name', type: 'string', required: false, default: 'world' },
    { name: 'times', type: 'integer', required: false, default: 3 },
  ],
  async ({ name, times }) => {
    const n = Number(times) || 0;
    return Array.from({ length: n }, (_, i) => `hello ${String(name)} #${i + 1}`).join('\n');
  },
);

task(
  'slow_work',
  [{ name: 'seconds', type: 'number', required: false, default: 0.3 }],
  async ({ seconds }) => {
    // Task-owned progress logging; blocking work would be offloaded by the task itself.
    log.info('slow_work start');
    await new Promise((r) => setTimeout(r, Number(seconds) * 1000));
    return `slow work done after ${String(seconds)}s`;
  },
);

task('boom', [], async () => {
  throw new Error('something went wrong');
});
