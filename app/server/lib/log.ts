import { appendFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { env } from '~/server/lib/config';

// Lightweight stand-in for the Python loguru logger. Logging output is not part of
// the user-facing behaviour contract; we keep the same call surface and write to
// console plus the LOG_PATH files (best effort) so operators still get server.log/error.log.
let filesReady = false;
function ensureFiles() {
  if (filesReady) return;
  try {
    mkdirSync(env.LOG_PATH, { recursive: true });
    filesReady = true;
  } catch {
    /* logging must never crash the app */
  }
}

function stamp() {
  return new Date().toISOString();
}

function write(level: string, file: string | null, args: unknown[]) {
  const line = `${stamp()} | ${level.toUpperCase().padEnd(7)} | ${args
    .map((a) => (typeof a === 'string' ? a : JSON.stringify(a)))
    .join(' ')}`;
  // eslint-disable-next-line no-console
  console.log(line);
  ensureFiles();
  if (file) {
    try {
      appendFileSync(join(env.LOG_PATH, file), line + '\n');
    } catch {
      /* ignore */
    }
  }
}

export const log = {
  trace: (...a: unknown[]) => write('trace', 'server.log', a),
  debug: (...a: unknown[]) => write('debug', 'server.log', a),
  info: (...a: unknown[]) => write('info', 'server.log', a),
  warning: (...a: unknown[]) => write('warning', 'server.log', a),
  error: (...a: unknown[]) => write('error', 'error.log', a),
  exception: (...a: unknown[]) => write('error', 'error.log', a),
};
