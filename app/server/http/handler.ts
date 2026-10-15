import { HttpError } from '~/server/lib/httpError';
import { CookieJar, getCookie, getRealIp, parseCookies } from '~/server/lib/auth';
import { bootstrap } from '~/server/lib/bootstrap';
import { isDebug } from '~/server/lib/config';
import { log } from '~/server/lib/log';
import { requireAdmin } from '~/server/service/security';
import type { LoginContext } from '~/server/service/security';

// Bridges React Router loaders/actions to the shared server-side service layer.
// One wrapper turns a service call into a spec-compliant HTTP Response:
//  - bootstraps the server on the first request (config/db/cache/jieba/scheduler)
//  - parses cookies + real ip (the FastAPI Request/Response equivalents)
//  - serialises thrown HttpError to { detail } with the original status code
//  - flushes any Set-Cookie operations the handler queued on its CookieJar

export interface HandlerCtx {
  request: Request;
  params: Record<string, string>;
  url: URL;
  cookies: Record<string, string>;
  realIp: string;
  jar: CookieJar;
  query: (name: string) => string | null;
  num: (name: string) => number | null;
  bool: (name: string) => boolean | null;
  json: <T>() => Promise<T>;
  formData: () => Promise<FormData>;
}

export interface ApiOptions {
  // When true, require an authenticated admin before running the handler (mirrors the
  // require_admin dependency the management routers carried).
  admin?: boolean;
}

export type Handler = (ctx: HandlerCtx) => Promise<unknown> | unknown;

interface RouteArgs {
  request: Request;
  params?: Record<string, string>;
}

// The FastAPI Request/Response pair consumed by security_service.
export function toLoginContext(ctx: HandlerCtx): LoginContext {
  return { cookies: ctx.cookies, jar: ctx.jar, status: 200 };
}

async function buildCtx({ request, params }: RouteArgs): Promise<HandlerCtx> {
  await bootstrap();
  const url = new URL(request.url);
  return {
    request,
    params: params ?? {},
    url,
    cookies: parseCookies(request),
    realIp: getRealIp(request),
    jar: new CookieJar(),
    query: (name) => url.searchParams.get(name),
    num: (name) => {
      const v = url.searchParams.get(name);
      return v === null ? null : Number(v);
    },
    bool: (name) => {
      const v = url.searchParams.get(name);
      return v === null ? null : v === 'true';
    },
    json: async <T,>() => (await request.json()) as T,
    formData: () => request.formData(),
  };
}

async function run(handler: Handler, opts: ApiOptions, args: RouteArgs): Promise<Response> {
  const ctx = await buildCtx(args);
  try {
    if (opts.admin) await requireAdmin(toLoginContext(ctx));
    const result = await handler(ctx);
    return toResponse(result, ctx.jar);
  } catch (e) {
    if (e instanceof HttpError) {
      const headers = new Headers(e.headers);
      ctx.jar.apply(headers);
      return Response.json({ detail: e.detail ?? null }, { status: e.status, headers });
    }
    if (isDebug) throw e;
    log.exception(`${ctx.request.method} ${ctx.url.pathname} ${String(e)}`);
    // Legacy ExceptionMiddleware answered unhandled errors with JSONResponse(None, 500).
    return Response.json(null, { status: 500 });
  }
}

function toResponse(result: unknown, jar: CookieJar): Response {
  const headers = new Headers();
  jar.apply(headers);
  if (result instanceof Response) {
    for (const [k, v] of result.headers) headers.set(k, v);
    return new Response(result.body, { status: result.status, headers });
  }
  headers.set('Content-Type', 'application/json');
  // FastAPI answered with a JSON document even when the handler returned None (`null`),
  // so an empty body would be a contract change.
  return new Response(JSON.stringify(result ?? null), { status: 200, headers });
}

// loader/action factories: match RR7's `(args) => Response` signature.
export const apiLoader = (handler: Handler, opts: ApiOptions = {}) =>
  (args: RouteArgs) => run(handler, opts, args);

export const apiAction = (handler: Handler, opts: ApiOptions = {}) =>
  (args: RouteArgs) => run(handler, opts, args);

// FastAPI registers each endpoint on one verb and answers anything else with
// 405 + `allow`. RR7 would instead throw a 400 "no loader/action" error, so the
// opposite verb is exported as an explicit refusal to keep the contract identical.
export const methodDenied = (allowed: string) => () =>
  Response.json({ detail: 'Method Not Allowed' }, { status: 405, headers: { allow: allowed } });

export { getCookie };
