import { createHmac } from 'node:crypto';
import { config, env } from '~/server/lib/config';

// Mirrors wwricu/service/security.py primitive: hmac_sign.
export function hmacSign(plain: string): string {
  return createHmac('sha256', Buffer.from(config().security.secret_key, 'base64'))
    .update(plain)
    .digest('hex');
}

export interface CookieAttrs {
  maxAge?: number;
  domain?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: 'lax' | 'strict' | 'none';
  path?: string;
}

// Serialize a cookie the way FastAPI's set_cookie does (Max-Age, Domain, Secure, HttpOnly, SameSite).
export function serializeCookie(name: string, value: string, attrs: CookieAttrs = {}): string {
  const parts = [`${name}=${encodeURIComponent(value)}`];
  if (attrs.maxAge !== undefined) parts.push(`Max-Age=${Math.floor(attrs.maxAge)}`);
  if (attrs.domain) parts.push(`Domain=${attrs.domain}`);
  parts.push(`Path=${attrs.path ?? '/'}`);
  if (attrs.secure) parts.push('Secure');
  if (attrs.httpOnly) parts.push('HttpOnly');
  if (attrs.sameSite) parts.push(`SameSite=${capitalize(attrs.sameSite)}`);
  return parts.join('; ');
}

function capitalize(s: string): string {
  return s[0].toUpperCase() + s.slice(1);
}

export function serializeDeleteCookie(name: string, attrs: CookieAttrs = {}): string {
  return serializeCookie(name, '', { ...attrs, maxAge: 0 });
}

// Default session cookie attributes (domain/secure/httpOnly/sameSite lax) as used in security.login.
export function sessionCookieAttrs(maxAge: number): CookieAttrs {
  return { maxAge, domain: env.BASE_DOMAIN, secure: true, httpOnly: true, sameSite: 'lax' };
}

export function parseCookies(request: Request): Record<string, string> {
  const header = request.headers.get('cookie') ?? '';
  const out: Record<string, string> = {};
  for (const pair of header.split(';')) {
    const idx = pair.indexOf('=');
    if (idx === -1) continue;
    const k = pair.slice(0, idx).trim();
    const v = pair.slice(idx + 1).trim();
    if (k) out[k] = decodeURIComponent(v);
  }
  return out;
}

export function getCookie(request: Request, name: string): string | undefined {
  return parseCookies(request)[name];
}

// Mirrors PerformanceMiddleware real_ip: X-Forwarded-For first hop.
export function getRealIp(request: Request): string {
  return (request.headers.get('x-forwarded-for') ?? '').split(',')[0].trim();
}

// Collects Set-Cookie headers the way FastAPI's Response object does across login/logout calls,
// so a single route handler can flush several cookies (including deletions) in one response.
export class CookieJar {
  readonly ops: string[] = [];

  set(name: string, value: string, attrs: CookieAttrs = {}): void {
    this.ops.push(serializeCookie(name, value, attrs));
  }

  delete(name: string, attrs: CookieAttrs = {}): void {
    this.ops.push(serializeDeleteCookie(name, attrs));
  }

  apply(headers: Headers): void {
    for (const op of this.ops) headers.append('set-cookie', op);
  }
}
