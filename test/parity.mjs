#!/usr/bin/env node
// Parity harness: legacy FastAPI (:8000) vs the RR7 port (:5199) on the same SQLite file.
//
// URL mapping: the legacy admin SPA reached the Python backend through a Vite proxy that
// stripped the /api prefix, so `/api/post/all` on RR7 is `/post/all` on the legacy server.
// The public /open/* + /image/* paths are identical on both.
//
// Volatile fields are normalised before diffing: presigned urls drop their query string,
// and counters/timestamps only have to exist (they change between the two requests).
//
// Two endpoints read per-process state, so the two servers must be equally warm for a strict
// comparison: /open/about returns the cached global counters (reset_sys_config only refreshes
// them behind post/update, post/status, post/delete, tag/create and tag/delete, so a freshly
// started backend reports 0 until its first such write), and POST /login consumes the IP token
// bucket. Restart both, or run the same writes against both, before trusting those two cases.

const VOLATILE_URL_KEYS = new Set(['url', 'location']);
const VOLATILE_VALUE_KEYS = new Set(['startup_timestamp']);

function normalize(value) {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      if (VOLATILE_URL_KEYS.has(k)) out[k] = typeof v === 'string' ? v.split('?')[0] : v;
      else if (VOLATILE_VALUE_KEYS.has(k)) out[k] = typeof v === 'number' ? '<present>' : v;
      else out[k] = normalize(v);
    }
    return out;
  }
  return value;
}

async function grab(base, path, init = {}) {
  const res = await fetch(base + path, init);
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text.slice(0, 300);
  }
  return { status: res.status, allow: res.headers.get('allow'), body: normalize(body) };
}

function diff(a, b, path = '') {
  if (a === b) return [];
  const ta = Array.isArray(a) ? 'array' : typeof a;
  const tb = Array.isArray(b) ? 'array' : typeof b;
  if (ta !== tb) return [`${path}: type ${ta} vs ${tb}`];
  if (ta === 'array') {
    if (a.length !== b.length) return [`${path}: length ${a.length} vs ${b.length}`];
    return a.flatMap((item, i) => diff(item, b[i], `${path}[${i}]`));
  }
  if (ta === 'object' && a && b) {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    return [...keys].flatMap((k) => diff(a[k], b[k], `${path}.${k}`));
  }
  return [`${path}: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`];
}

// `rr` is the RR7 path; the legacy path is derived by stripping /api (proxy behaviour).
// Multipart case: carries the form fields on the entry instead of a JSON payload.
function form(path, fields) {
  const entry = ['POST', path];
  entry.form = fields;
  return entry;
}

const cases = [
  // ---- public API (consumed by the external blog page) ----
  ['GET', '/open/about'],
  ['POST', '/open/post/all', { page_index: 1, page_size: 3 }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 3, status: 'draft' }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 2, category: '杂谈与抱怨' }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 2, tag_list: ['好图'] }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 1, tag_list: ['不存在的标签'] }],
  ['GET', '/open/tags/post_tag'],
  ['GET', '/open/tags/post_category'],
  ['GET', '/open/post/search?keyword=星'],
  ['GET', '/open/post/search?keyword=prox'],
  ['GET', '/open/post/search?keyword=  '],
  ['GET', '/open/post/detail/5103425117'],
  ['GET', '/open/post/detail/3572305464'],
  ['GET', '/open/post/detail/999999'],

  // ---- public API validation + method contracts ----
  ['GET', '/open/tags/bogus_type'],
  ['GET', '/open/tags/'],
  ['GET', '/open/post/search'],
  ['GET', '/open/post/search?keyword='],
  ['GET', '/open/post/search?keyword=' + 'x'.repeat(200)],
  ['GET', '/open/post/detail/abc'],
  ['GET', '/open/post/detail/1.5'],
  ['GET', '/open/post/detail/-1'],
  ['POST', '/open/post/all', undefined], // no body at all
  ['POST', '/open/post/all', {}], // missing mandatory page fields
  ['POST', '/open/post/all', { page_index: 'x', page_size: 1 }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 1, status: 'bogus' }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 1, tag_list: 'abc' }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 1, tag_list: [1] }],
  ['POST', '/open/post/all', { page_index: 1, page_size: 1, category: 5 }],
  ['POST', '/open/post/all', true], // non-object body
  ['GET', '/open/post/all'], // wrong verb → 405 + allow
  ['POST', '/open/about'],
  ['POST', '/open/tags/post_tag'],
  ['POST', '/open/post/detail/5103425117'],
  ['POST', '/open/post/search?keyword=星'],

  // ---- admin API, unauthenticated (cookie guard parity; /api → legacy root) ----
  ['POST', '/api/post/all', { page_index: 1, page_size: 1 }],
  ['GET', '/api/post/detail/5103425117'],
  ['GET', '/api/info'],
  ['GET', '/api/manage/trash'],
  ['GET', '/api/manage/config?key=about_content'],
  ['GET', '/api/task/running'],
  ['GET', '/api/tag/all'],

  // ---- admin API behaviour (uvicorn dev ⇒ legacy is_admin short-circuits on __debug__) ----
  ['POST', '/api/post/all', { page_index: 1, page_size: 5 }],
  ['POST', '/api/post/all', { page_index: 2, page_size: 5 }],
  ['POST', '/api/post/all', { page_index: 1, page_size: 5, status: 'draft' }],
  ['POST', '/api/post/all', { page_index: 1, page_size: 5, deleted: true }],
  ['GET', '/api/post/detail/999999'],
  ['GET', '/api/post/detail/abc'],
  ['GET', '/api/post/status/5103425117'],
  ['GET', '/api/post/status/5103425117?status=bogus'],
  ['GET', '/api/post/delete/999999'],
  ['POST', '/api/tag/all', { page_index: 1, page_size: 0, type: 'post_tag' }],
  ['POST', '/api/tag/all', {}],
  ['POST', '/api/tag/all', { type: 'post_category' }],
  ['GET', '/api/manage/trash/all'],
  ['GET', '/api/manage/config/get?key=about_content'],
  ['GET', '/api/manage/config/get'],
  ['GET', '/api/manage/config/get?key=bogus'],
  ['GET', '/api/manage/config/get?key=password'],
  ['GET', '/api/manage/config/get?key=totp_secret'],
  ['GET', '/api/manage/database'],
  ['GET', '/api/manage/database?action=bogus'],
  ['GET', '/api/manage/totp/confirm'],
  ['POST', '/api/task/search', {}],
  ['POST', '/api/task/search', { keyword: 'slow' }],
  ['POST', '/api/task/search', { keyword: 1 }],

  // ---- admin API request-object validation (all rejected before any write) ----
  ['POST', '/api/post/all', { page_index: 1 }],
  ['POST', '/api/post/all', { page_index: 1, page_size: 1, tag_list: [2] }],
  ['POST', '/api/post/update', { id: 1 }],
  ['POST', '/api/post/update', { id: 'x', title: 't', preview: 'p', status: 'draft', content: 'c', tag_id_list: [] }],
  ['POST', '/api/tag/all', { type: 'bogus' }],
  ['POST', '/api/tag/all', { page_index: 'x', page_size: 1 }],
  ['POST', '/api/tag/all', { page_index: 1, page_size: 1, type: 'post_tag' }],
  ['POST', '/api/tag/create', {}],
  ['POST', '/api/tag/create', { name: 'x'.repeat(33) }],
  ['POST', '/api/manage/trash/edit', { id: 1 }],
  ['POST', '/api/manage/trash/edit', { id: 1, type: 'Bogus' }],
  ['POST', '/api/manage/config/set', { key: 'bogus' }],
  ['POST', '/api/manage/user', { reset: 'maybe' }],
  ['POST', '/api/task/search', { keyword: null }],
  ['POST', '/api/task/run', {}],

  // ---- pydantic null semantics -----------------------------------------------------
  // `x: T | None = None` accepts an explicit null; a mandatory field and the plain-typed
  // defaults (`deleted: bool = False`, `keyword: str = ''`, `params: dict = {}`) answer
  // with the matching *_type issue. Every case here fails validation, so nothing is written.
  ['POST', '/api/post/all', { page_index: null, page_size: 1 }],
  ['POST', '/api/post/all', { page_index: 1, page_size: 1, deleted: null }],
  ['POST', '/api/post/all', { page_index: 1, page_size: 1, tag_list: null, category: null, status: null }],
  ['POST', '/api/post/update', { id: null, title: null, preview: null, status: null, content: null, tag_id_list: null, cover_id: null, category_id: null }],
  ['POST', '/api/tag/all', { page_index: null, page_size: null, type: null }],
  ['POST', '/api/tag/create', { id: null, name: null, type: null }],
  ['POST', '/api/manage/trash/edit', { id: null, type: null }],
  ['POST', '/api/manage/trash/edit', { id: 1, type: 'post', delete: 'maybe' }],
  ['POST', '/api/manage/config/set', { key: null, value: null }],
  ['POST', '/api/manage/user', { username: 1, reset: null }],
  ['POST', '/api/task/run', { name: null }],
  ['POST', '/api/task/run', { name: 'demo', params: null }],
  ['POST', '/api/login', { username: null, password: 'x' }],

  // ---- multipart form validation (POST /post/upload) -------------------------------
  // Every case fails FastAPI's form validation, so nothing reaches storage or the DB.
  // '@file' marks a real file part; any other value is sent as a plain text field.
  form('/api/post/upload', {}),
  form('/api/post/upload', { file: '@file' }),
  form('/api/post/upload', { file: '@file', post_id: 'abc' }),
  form('/api/post/upload', { file: '@file', post_id: 'true' }),
  form('/api/post/upload', { file: '@file', post_id: '1.5' }),
  form('/api/post/upload', { file: '@file', post_id: '1', file_type: 'bogus' }),
  form('/api/post/upload', { post_id: '1' }),
  form('/api/post/upload', { file: 'hello', post_id: '1', file_type: 'image' }),
  // Valid form for a post id that does not exist (the dev DB has no id 1): both backends look
  // the post up before touching storage, so this ends in the same 404 without writing anything.
  form('/api/post/upload', { file: '@file', post_id: '1', file_type: 'image' }),
];

// Point RR_BASE at `react-router-serve` to compare the legacy service with a production
// build instead of the dev server.
const PY = process.env.PY_BASE ?? 'http://127.0.0.1:8000';
const RR = process.env.RR_BASE ?? 'http://localhost:5199';

let failures = 0;
for (const entry of cases) {
  const [method, rrPath, payload] = entry;
  const pyPath = rrPath.replace(/^\/api/, '') || '/';
  const formFields = entry.form;
  const label = `${method} ${rrPath}${formFields ? ' form ' + JSON.stringify(formFields) : payload === undefined ? '' : ' ' + JSON.stringify(payload)}`;

  const init = () => {
    if (formFields) {
      const fd = new FormData();
      for (const [k, v] of Object.entries(formFields)) {
        fd.append(k, v === '@file' ? new File(['hi'], 'probe.txt', { type: 'text/plain' }) : v);
      }
      // Let fetch set the multipart boundary; only the method and body matter here.
      return { method, body: fd };
    }
    return {
      method,
      headers: payload ? { 'Content-Type': 'application/json' } : undefined,
      body: payload === undefined ? undefined : JSON.stringify(payload),
    };
  };

  const a = await grab(PY, pyPath, init());
  const b = await grab(RR, rrPath, init());

  // The login token bucket is per-process memory, so the two servers can sit at different
  // points of the same drain (see test/login-bucket.mjs for the shared semantics): one may
  // answer 422 while the other is already out of tokens and answers 429. Such a pair counts
  // as a match.
  const bucketDrift =
    rrPath === '/api/login' &&
    ((a.status === 429 && b.status === 422) || (a.status === 422 && b.status === 429));

  const problems = [];
  if (a.status !== b.status && !bucketDrift) problems.push(`status: py=${a.status} rr=${b.status}`);
  if (a.allow !== b.allow) problems.push(`allow: py=${a.allow} rr=${b.allow}`);
  if (!bucketDrift) problems.push(...diff(a.body, b.body));

  // Raw text bodies (non-JSON) need a separate look: FastAPI's 404 page vs our JSON.
  const shown = problems.length
    ? ''
    : `  [${a.status}]`;

  if (problems.length === 0) {
    console.log(`OK   ${label}${shown}`);
  } else {
    failures++;
    console.log(`DIFF ${label}  (py ${pyPath} [${a.status}] / rr [${b.status}])`);
    for (const p of problems.slice(0, 6)) console.log(`     ${p}`);
    if (problems.length > 6) console.log(`     ... ${problems.length - 6} more`);
    if (typeof a.body === 'string' || typeof b.body === 'string') {
      console.log(`     py body: ${JSON.stringify(a.body).slice(0, 240)}`);
      console.log(`     rr body: ${JSON.stringify(b.body).slice(0, 240)}`);
    }
  }
}

console.log(`\n${failures === 0 ? 'ALL PARITY CHECKS PASSED' : failures + ' PARITY DIFFS'}`);
process.exit(failures === 0 ? 0 : 1);
