import bcrypt from 'bcryptjs';
import { randomUUID } from 'node:crypto';
import { sysCache } from '~/server/lib/caches';
import { CookieJar, hmacSign, serializeCookie, serializeDeleteCookie, sessionCookieAttrs } from '~/server/lib/auth';
import { defaultBucket, loginBucket } from '~/server/lib/tokenBucket';
import { config, env, isDebug } from '~/server/lib/config';
import { badRequest, forbidden, tooManyRequests, unauthorized } from '~/server/lib/httpError';
import { CommonConst, HttpErrorDetail, TimeConst } from '~/server/domain/constants';
import { ConfigKey, type ConfigKeyEnum } from '~/server/domain/enum';
import { getConfig, verifyTotp } from '~/server/service/manage';
import type { LoginRO, LoginVO } from '~/server/domain/types';

// Mirrors wwricu/service/security.py.

// ---- Request/response context ----
// FastAPI handed the endpoint a `Request` (for cookies) and a mutable `Response` (for
// Set-Cookie / status). React Router actions do the same via the request + a CookieJar,
// and we return the status code from authenticate().

export interface LoginContext {
  cookies: Record<string, string | undefined>;
  jar: CookieJar;
  status: number; // caller initialises to 200; authenticate may set it to 401
}

// ---- Rate limiters ----

export async function loginLimiter(realIp: string): Promise<void> {
  const ok = loginBucket().cost(realIp, config().security.login_ip_span / config().security.login_ip_times);
  if (!ok) {
    console.warn(`${realIp} exceeded login rate limit`);
    throw tooManyRequests();
  }
}

// login_limiter's post-yield cleanup (reset the bucket once the request finishes).
export function loginLimiterCleanup(realIp: string): void {
  loginBucket().reset(realIp);
}

export async function imageLimiter(realIp: string): Promise<void> {
  const id = formatBucketId(CommonConst.IMAGE_IP_BUCKET, realIp);
  if (!(await defaultBucket.allow(id, config().security.image_ip_qps))) {
    console.warn(`${realIp} exceeded image rate limit`);
    throw tooManyRequests();
  }
}

export async function openLimiter(realIp: string): Promise<void> {
  const id = formatBucketId(CommonConst.OPEN_IP_BUCKET, realIp);
  if (!(await defaultBucket.allow(id, config().security.open_ip_qps))) {
    console.warn(`${realIp} exceeded open rate limit`);
    throw tooManyRequests();
  }
}

function formatBucketId(template: string, ip: string): string {
  return template.replace('{ip}', ip);
}

// ---- Authentication ----

export async function authenticate(loginRequest: LoginRO, ctx: LoginContext): Promise<LoginVO> {
  const sessionId = randomUUID().replace(/-/g, ''); // uuid4().hex
  const session2faId = ctx.cookies[CommonConst.SESSION_ID_2FA];

  const secret = getConfig(ConfigKey.TOTP_SECRET);
  const enforce = getConfig(ConfigKey.TOTP_ENFORCE);

  if (session2faId && (!enforce || !loginRequest.totp)) {
    sysCache.delete(session2faId);
    ctx.jar.delete(CommonConst.SESSION_ID_2FA);
  } else if (session2faId && enforce && secret && loginRequest.totp && sysCache.get(session2faId)) {
    if (!verifyTotp(secret, loginRequest.totp)) {
      console.warn(`${loginRequest.username} wrong totp`);
      throw unauthorized(HttpErrorDetail.WRONG_TOTP);
    }
    sysCache.delete(session2faId);
    ctx.jar.delete(CommonConst.SESSION_ID_2FA);
    await login(sessionId, ctx.jar);
    return {};
  }

  if (!(await verifyCredentials(loginRequest))) {
    console.warn(`${loginRequest.username} login failure`);
    throw unauthorized(HttpErrorDetail.WRONG_PASSWORD);
  }

  if (getConfig(ConfigKey.TOTP_ENFORCE)) {
    sysCache.set(sessionId, true, TimeConst.TOTP_EXPIRATION);
    ctx.jar.set(
      CommonConst.SESSION_ID_2FA,
      sessionId,
      { maxAge: TimeConst.TOTP_EXPIRATION, secure: true, httpOnly: true, sameSite: 'lax' },
    );
    ctx.status = 401;
    return { detail: HttpErrorDetail.NEED_TOTP };
  }

  await login(sessionId, ctx.jar);
  return {};
}

export async function requireAdmin(ctx: LoginContext): Promise<void> {
  if (!(await isAdmin(ctx))) throw unauthorized();
}

export async function isAdmin(ctx: LoginContext): Promise<boolean> {
  if (isDebug) return true;

  const sessionId = ctx.cookies[CommonConst.SESSION_ID];
  const cookieSign = ctx.cookies[CommonConst.COOKIE_SIGN];
  if (sessionId === undefined || cookieSign === undefined) return false;

  const issueTime = sysCache.get<number>(sessionId);
  const nowSec = Math.floor(Date.now() / 1000);
  if (
    typeof issueTime !== 'number' ||
    issueTime < 0 ||
    nowSec - issueTime >= TimeConst.COOKIE_MAX_AGE ||
    hmacSign(sessionId) !== cookieSign
  ) {
    return false;
  }

  if (issueTime + TimeConst.ONE_DAY_SECONDS < nowSec) {
    await login(sessionId, ctx.jar);
  }
  return true;
}

async function login(sessionId: string, jar: CookieJar): Promise<void> {
  sysCache.set(sessionId, Math.floor(Date.now() / 1000), TimeConst.COOKIE_MAX_AGE);
  const attrs = sessionCookieAttrs(TimeConst.COOKIE_MAX_AGE);
  jar.set(CommonConst.SESSION_ID, sessionId, attrs);
  jar.set(CommonConst.COOKIE_SIGN, hmacSign(sessionId), attrs);
}

export async function logout(ctx: LoginContext): Promise<void> {
  const sessionId = ctx.cookies[CommonConst.SESSION_ID];
  if (sessionId === undefined) return;
  // delete_cookie(name, domain=BASE_DOMAIN) — matches Python logout.
  ctx.jar.delete(CommonConst.SESSION_ID, { domain: env.BASE_DOMAIN });
  ctx.jar.delete(CommonConst.COOKIE_SIGN, { domain: env.BASE_DOMAIN });
  sysCache.delete(sessionId);
}

// ---- Credential verification (throttled: one concurrent bcrypt compare, 2s queue timeout) ----

const throttle = makeThrottle(1, 2.0);

export const verifyCredentials = throttle(async function verifyCredentials(request: LoginRO): Promise<boolean> {
  let username = getConfig(ConfigKey.USERNAME) ?? '';
  let password = getConfig(ConfigKey.PASSWORD) ?? '';
  if (!username) username = config().security.username;
  if (!password) password = config().security.password;
  const hash = Buffer.from(password, 'base64').toString('utf-8');
  const ok = await bcrypt.compare(request.password ?? '', hash);
  return ok && (request.username ?? '') === username;
});

type AsyncFn = (...args: any[]) => Promise<any>;

function makeThrottle(concurrent: number, timeoutSec: number) {
  let active = 0;
  const waiting: Array<() => void> = [];

  function acquire(): Promise<void> {
    if (active < concurrent) {
      active += 1;
      return Promise.resolve();
    }
    return new Promise<void>((resolve, reject) => {
      const grant = () => {
        clearTimeout(timer);
        resolve();
      };
      const timer = setTimeout(() => {
        const idx = waiting.indexOf(grant);
        if (idx >= 0) waiting.splice(idx, 1);
        reject(tooManyRequests());
      }, timeoutSec * 1000);
      waiting.push(grant);
    });
  }

  function releaseSlot(): void {
    active -= 1;
    const next = waiting.shift();
    if (next) {
      active += 1;
      next();
    }
  }

  return function wrap(fn: AsyncFn): AsyncFn {
    return async (...args: any[]) => {
      await acquire();
      try {
        return await fn(...args);
      } finally {
        releaseSlot();
      }
    };
  };
}

// Re-export cookie serializers for route handlers that set them directly.
export { serializeCookie, serializeDeleteCookie };
export { badRequest, forbidden };
export type { ConfigKeyEnum };
