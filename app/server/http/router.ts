import { HttpError, forbidden, notAcceptable, notFound } from '~/server/lib/httpError';
import { CookieJar, getRealIp, parseCookies } from '~/server/lib/auth';
import { bootstrap } from '~/server/lib/bootstrap';
import { isDebug } from '~/server/lib/config';
import { log } from '~/server/lib/log';
import { ConfigKey, DatabaseAction, EntityType, formatKey, type ConfigKeyEnum, type EntityTypeEnum, type TagTypeEnum } from '~/server/domain/enum';
import { CacheKey, PostStatus } from '~/server/domain/enum';
import type { DatabaseActionEnum } from '~/server/domain/enum';
import {
  parseConfigRO,
  parseLoginRO,
  parsePathInt,
  parsePostRequestRO,
  parsePostUpdateRO,
  parseQueryBool,
  parseQueryEnum,
  parseQueryStr,
  parseTagRequestRO,
  parseTagRO,
  parseTaskRunRO,
  parseTaskSearchRO,
  parseTrashBinRO,
  parseUploadFormRO,
  parseUserRO,
  readJsonObject,
} from '~/server/domain/validate';
import { queryCache, postCache, postStatusCache } from '~/server/lib/caches';
import * as postService from '~/server/service/post';
import * as tagService from '~/server/service/tag';
import * as manageService from '~/server/service/manage';
import * as securityService from '~/server/service/security';
import * as taskService from '~/server/service/task';
import * as commonService from '~/server/service/common';
import * as postDb from '~/server/db/post';
import * as tagDb from '~/server/db/tag';
import { getDetail } from '~/server/service/post';
import type { LoginContext } from '~/server/service/security';
import type { ConfigRO, LoginRO, PostRequestRO, PostUpdateRO, TagRO, TagRequestRO, TrashBinRO, UserRO, TaskRunRO, TaskSearchRO, LoginVO } from '~/server/domain/types';

// In-process dispatcher replacing the FastAPI api_router + the admin SPA's /api proxy.
// The admin pages call /api/<legacy path>; each maps 1:1 to the same service functions
// the legacy Python api/*.py wired up, so behaviour is unchanged while the browser only
// ever talks to this single RR7 server (no second backend, no cross-service HTTP).

function json(data: unknown, jar?: CookieJar, status = 200): Response {
  const headers = new Headers({ 'Content-Type': 'application/json' });
  if (jar) jar.apply(headers);
  // FastAPI always emitted a JSON document: an endpoint returning None was the literal
  // `null` body, not the empty body RR7 would produce from undefined.
  return new Response(JSON.stringify(data ?? null), { status, headers });
}

function redirect(url: string, status = 307): Response {
  return new Response(null, { status, headers: { location: url } });
}

interface Ctx {
  request: Request;
  url: URL;
  cookies: Record<string, string>;
  realIp: string;
  jar: CookieJar;
  path: string; // legacy path, e.g. "post/all" (no leading /api/ or slash)
  params: Record<string, string>; // trailing dynamic segment when the handler needs it
  ro: <T>(parse: (body: Record<string, unknown>) => T) => Promise<T>;
  form: () => Promise<FormData>;
}

function loginCtx(ctx: Ctx): LoginContext {
  return { cookies: ctx.cookies, jar: ctx.jar, status: 200 };
}

// ---- Open (public) — kept here so /api mirrors the legacy surface exactly; the
// canonical /open/* + /image/* routes (for the external blog-page) live in app/routes. ----

// ---- Auth ----
async function login(ctx: Ctx): Promise<Response> {
  // security_service.login_limiter is a dependency-with-yield: it drains a token before the
  // body is validated and only refills (reset) when the endpoint returns without raising.
  // A 422 / 401 / 429 therefore leaves the bucket drained — that is what makes login_ip_times
  // failed attempts per span lock an IP out — while a completed attempt (including the
  // need-totp 401 response body) restores it. An unconditional finally-reset would neuter
  // the limiter.
  await securityService.loginLimiter(ctx.realIp);
  const body = await ctx.ro(parseLoginRO);
  const lc = loginCtx(ctx);
  const vo: LoginVO = await securityService.authenticate(body, lc);
  securityService.loginLimiterCleanup(ctx.realIp);
  return json(vo, ctx.jar, lc.status);
}

async function logout(ctx: Ctx): Promise<Response> {
  await securityService.logout(loginCtx(ctx));
  return json(null, ctx.jar);
}

async function info(): Promise<Response> {
  return json(null);
}

// ---- Post management ----
function allPosts(ctx: Ctx, isPublic: boolean) {
  return async () => {
    const req = await ctx.ro(parsePostRequestRO);
    const query = postService.buildQuery(req, { public: isPublic });
    return postService.listByQuery(query);
  };
}

async function createPost(): Promise<Response> {
  const id = 1_000_000_000 + Math.floor(Math.random() * 9_000_000_000);
  const row = (await import('~/server/db/common')).insert(postTable(), 'id', { id, status: PostStatus.DRAFT });
  return json(getDetail(row as never));
}

function postTable(): string {
  // resolve the blog_post table without importing the const from a service-only module
  return 'wwr_blog_post';
}

async function getPostDetail(ctx: Ctx): Promise<Response> {
  const postId = parsePathInt(ctx.params.id, 'post_id');
  const post = postDb.findById(postId);
  if (!post) return json(null);
  return json(getDetail(post));
}

async function updatePost(ctx: Ctx): Promise<Response> {
  const req = await ctx.ro(parsePostUpdateRO);
  const detail = postService.update(req);
  await commonService.resetSysConfig();
  postCache.delete(formatKey(CacheKey.POST, { id: req.id }));
  queryCache.deleteAll();
  return json(detail);
}

async function updatePostStatus(ctx: Ctx): Promise<Response> {
  const postId = parsePathInt(ctx.params.id, 'post_id');
  const status = parseQueryEnum(ctx.url.searchParams.get('status'), 'status', Object.values(PostStatus));
  postService.updateStatus(postId, status);
  await commonService.resetSysConfig();
  const key = formatKey(CacheKey.POST, { id: postId });
  postStatusCache.delete(key);
  postCache.delete(key);
  queryCache.deleteAll();
  return json(null);
}

async function deletePost(ctx: Ctx): Promise<Response> {
  const postId = parsePathInt(ctx.params.id, 'post_id');
  const post = postDb.findById(postId);
  if (!post) throw notFound();
  if (post.status === PostStatus.PUBLISHED) throw forbiddenError();
  postDb.updateSelective(postId, { deleted: true });
  await commonService.resetSysConfig();
  return json(null);
}

function forbiddenError(): HttpError {
  // HTTPException(403) without a detail → Starlette's phrase.
  return forbidden();
}

async function uploadPostFile(ctx: Ctx): Promise<Response> {
  const { file, post_id, file_type } = parseUploadFormRO(await ctx.form());
  const buf = new Uint8Array(await file.arrayBuffer());
  const vo = await postService.uploadFile(
    { filename: file.name, size: file.size, data: buf },
    post_id,
    file_type,
  );
  return json(vo);
}

// ---- Tag management ----
async function createTag(ctx: Ctx): Promise<Response> {
  const req = await ctx.ro(parseTagRO);
  const vo = await tagService.create(req);
  queryCache.deleteAll();
  await commonService.resetSysConfig();
  return json(vo);
}

async function getAllTags(ctx: Ctx): Promise<Response> {
  const req = await ctx.ro(parseTagRequestRO);
  const rows = tagDb.findByCriteria({
    // tag_api.get_tags_api forwards the RO as-is: an explicit null means "no type filter",
    // while an omitted field already carries the model default (post_tag) after validation.
    type: (req.type ?? null) as TagTypeEnum | null,
    page_index: req.page_index ?? null,
    page_size: req.page_size ?? null,
  });
  return json(rows.map((t) => ({ id: t.id, name: t.name, type: t.type, count: t.count ?? null })));
}

async function updateTag(ctx: Ctx): Promise<Response> {
  const req = await ctx.ro(parseTagRO);
  const vo = await tagService.update(req);
  queryCache.deleteAll();
  return json(vo);
}

async function deleteTag(ctx: Ctx): Promise<Response> {
  const tagId = parsePathInt(ctx.params.id, 'tag_id');
  tagDb.updateSelective(tagId, { deleted: true });
  queryCache.deleteAll();
  await commonService.resetSysConfig();
  return json(null);
}

// ---- Manage ----
async function trashAll(): Promise<Response> {
  return json(manageService.listTrash());
}

async function trashEdit(ctx: Ctx): Promise<Response> {
  const ro = await ctx.ro(parseTrashBinRO);
  if (ro.type === EntityType.POST_IMAGE || ro.type === EntityType.POST_COVER) {
    await postService.processResourceTrash(ro);
    return json(null);
  }
  if (ro.type === EntityType.BLOG_POST) {
    postService.processTrash(ro);
  } else {
    await tagService.processTrash(ro);
  }
  queryCache.deleteAll();
  return json(null);
}

async function database(ctx: Ctx): Promise<Response> {
  const action = parseQueryEnum(ctx.url.searchParams.get('action'), 'action', Object.values(DatabaseAction));
  if (action === DatabaseAction.RESTORE) {
    const { restore } = await import('~/server/lib/db');
    restore();
    return json(null);
  }
  if (action === DatabaseAction.BACKUP) {
    const { backup } = await import('~/server/lib/db');
    await backup();
    return json(null);
  }
  if (action === DatabaseAction.DOWNLOAD) {
    const { config } = await import('~/server/lib/config');
    const { storageGetObject } = await import('~/server/lib/storage');
    const file = config().database.database;
    const data = await storageGetObject(file);
    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${file}"`,
      },
    });
  }
  return json(null);
}

async function configSet(ctx: Ctx): Promise<Response> {
  const ro = await ctx.ro(parseConfigRO);
  if (ro.key !== ConfigKey.ABOUT_CONTENT) throw notAcceptable();
  if (ro.value === null || ro.value === undefined) {
    manageService.deleteConfig([ro.key]);
    return json(null);
  }
  manageService.setConfig(ro.key, ro.value);
  return json(null);
}

async function configGet(ctx: Ctx): Promise<Response> {
  const key = parseQueryEnum(ctx.url.searchParams.get('key'), 'key', Object.values(ConfigKey));
  if (key === ConfigKey.PASSWORD || key === ConfigKey.TOTP_SECRET) throw notAcceptable();
  return json(manageService.getConfig(key));
}

async function userConfig(ctx: Ctx): Promise<Response> {
  const ro = await ctx.ro(parseUserRO);
  await manageService.updateAdminUser(ro);
  if (ro.username != null || ro.password != null || ro.reset === true) {
    await securityService.logout(loginCtx(ctx));
  }
  return json(null, ctx.jar);
}

async function totpEnforce(ctx: Ctx): Promise<Response> {
  const enforce = parseQueryBool(ctx.url.searchParams.get('enforce'), 'enforce');
  return json(manageService.enforceTotp(enforce));
}

async function totpConfirm(ctx: Ctx): Promise<Response> {
  const totp = parseQueryStr(ctx.url.searchParams.get('totp'), 'totp');
  manageService.confirmTotp(totp);
  return json(null);
}

// ---- Task ----
async function taskSearch(ctx: Ctx): Promise<Response> {
  const ro = await ctx.ro(parseTaskSearchRO);
  return json(taskService.search(ro));
}

async function taskRun(ctx: Ctx): Promise<Response> {
  const ro = await ctx.ro(parseTaskRunRO);
  return json(taskService.run(ro));
}

function taskRunning(): Response {
  return json(taskService.listStates());
}

type Matcher = (ctx: Ctx) => Promise<Response>;

interface Route {
  method: 'GET' | 'POST';
  // regex over the legacy path; named groups feed ctx.params
  re: RegExp;
  admin: boolean;
  match: (m: RegExpMatchArray) => Record<string, string>;
  handler: Matcher;
}

const routes: Route[] = [
  { method: 'POST', re: /^login$/, admin: false, match: () => ({}), handler: login },
  { method: 'GET', re: /^logout$/, admin: true, match: () => ({}), handler: logout },
  { method: 'GET', re: /^info$/, admin: true, match: () => ({}), handler: () => info() },

  { method: 'POST', re: /^post\/all$/, admin: true, match: () => ({}), handler: async (c) => json(await allPosts(c, false)()) },
  { method: 'GET', re: /^post\/create$/, admin: true, match: () => ({}), handler: () => createPost() },
  { method: 'GET', re: /^post\/detail\/(?<id>[^/]+)$/, admin: true, match: (m) => ({ id: m.groups!.id }), handler: getPostDetail },
  { method: 'POST', re: /^post\/update$/, admin: true, match: () => ({}), handler: updatePost },
  { method: 'GET', re: /^post\/status\/(?<id>[^/]+)$/, admin: true, match: (m) => ({ id: m.groups!.id }), handler: updatePostStatus },
  { method: 'GET', re: /^post\/delete\/(?<id>[^/]+)$/, admin: true, match: (m) => ({ id: m.groups!.id }), handler: deletePost },
  { method: 'POST', re: /^post\/upload$/, admin: true, match: () => ({}), handler: uploadPostFile },

  { method: 'POST', re: /^tag\/create$/, admin: true, match: () => ({}), handler: createTag },
  { method: 'POST', re: /^tag\/all$/, admin: true, match: () => ({}), handler: getAllTags },
  { method: 'POST', re: /^tag\/update$/, admin: true, match: () => ({}), handler: updateTag },
  { method: 'GET', re: /^tag\/delete\/(?<id>[^/]+)$/, admin: true, match: (m) => ({ id: m.groups!.id }), handler: deleteTag },

  { method: 'GET', re: /^manage\/trash\/all$/, admin: true, match: () => ({}), handler: () => trashAll() },
  { method: 'POST', re: /^manage\/trash\/edit$/, admin: true, match: () => ({}), handler: trashEdit },
  { method: 'GET', re: /^manage\/database$/, admin: true, match: () => ({}), handler: database },
  { method: 'POST', re: /^manage\/config\/set$/, admin: true, match: () => ({}), handler: configSet },
  { method: 'GET', re: /^manage\/config\/get$/, admin: true, match: () => ({}), handler: configGet },
  { method: 'POST', re: /^manage\/user$/, admin: true, match: () => ({}), handler: userConfig },
  { method: 'GET', re: /^manage\/totp\/enforce$/, admin: true, match: () => ({}), handler: totpEnforce },
  { method: 'GET', re: /^manage\/totp\/confirm$/, admin: true, match: () => ({}), handler: totpConfirm },

  { method: 'POST', re: /^task\/search$/, admin: true, match: () => ({}), handler: taskSearch },
  { method: 'POST', re: /^task\/run$/, admin: true, match: () => ({}), handler: taskRun },
  { method: 'GET', re: /^task\/running$/, admin: true, match: () => ({}), handler: async () => taskRunning() },
];

async function requireAdmin(ctx: Ctx): Promise<void> {
  await securityService.requireAdmin(loginCtx(ctx));
}

export async function dispatch(request: Request, legacyPath: string): Promise<Response> {
  await bootstrap();
  const url = new URL(request.url);
  const method = request.method.toUpperCase();

  const ctx: Ctx = {
    request,
    url,
    cookies: parseCookies(request),
    realIp: getRealIp(request),
    jar: new CookieJar(),
    path: legacyPath,
    params: {},
    ro: async <T>(parse: (body: Record<string, unknown>) => T): Promise<T> =>
      parse(await readJsonObject(request)),
    form: () => request.formData(),
  };

  const route = routes.find((r) => r.method === method && r.re.test(legacyPath));
  if (!route) {
    // FastAPI matched the path first and the verb second, so an existing endpoint called
    // with the wrong verb was a 405 + `allow`, not the 404 RR's router would produce.
    const allowed = [...new Set(routes.filter((r) => r.re.test(legacyPath)).map((r) => r.method))];
    if (allowed.length > 0) {
      return Response.json(
        { detail: 'Method Not Allowed' },
        { status: 405, headers: { allow: allowed.join(', ') } },
      );
    }
    return Response.json({ detail: 'Not Found' }, { status: 404 });
  }
  const m = legacyPath.match(route.re);
  ctx.params = route.match(m as RegExpMatchArray);

  try {
    if (route.admin) await requireAdmin(ctx);
    return await route.handler(ctx);
  } catch (e) {
    if (e instanceof HttpError) {
      const headers = new Headers(e.headers);
      ctx.jar.apply(headers);
      return Response.json({ detail: e.detail ?? null }, { status: e.status, headers });
    }
    if (isDebug) throw e;
    log.exception(`api ${method} /api/${legacyPath} ${String(e)}`);
    // Legacy ExceptionMiddleware answered unhandled errors with JSONResponse(None, 500).
    return Response.json(null, { status: 500 });
  }
}
