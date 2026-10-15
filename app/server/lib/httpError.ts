// Stand-in for FastAPI's HTTPException: thrown from the service layer and translated
// into a JSON Response (with the same status code + detail) by the route handlers.
// Keeps the wire contract identical to the previous Python backend.

export class HttpError extends Error {
  status: number;
  detail: unknown;
  headers?: Record<string, string>;

  constructor(status: number, detail: unknown = null) {
    super(typeof detail === 'string' ? detail : `HTTP ${status}`);
    this.name = 'HttpError';
    this.status = status;
    this.detail = detail;
  }
}

// Starlette's HTTPException defaults an omitted detail to http.HTTPStatus(code).phrase,
// and the admin pages show that string (handleResponse falls back to response.statusText
// only when the payload has no detail). Same table, so an error without an explicit
// message reads the same as it did on the Python backend.
const STATUS_PHRASE: Record<number, string> = {
  400: 'Bad Request',
  401: 'Unauthorized',
  403: 'Forbidden',
  404: 'Not Found',
  405: 'Method Not Allowed',
  406: 'Not Acceptable',
  408: 'Request Timeout',
  409: 'Conflict',
  411: 'Length Required',
  413: 'Content Too Large',
  415: 'Unsupported Media Type',
  422: 'Unprocessable Content',
  429: 'Too Many Requests',
  500: 'Internal Server Error',
  502: 'Bad Gateway',
  503: 'Service Unavailable',
};

export const statusPhrase = (status: number): string => STATUS_PHRASE[status] ?? `HTTP ${status}`;

// Common constructors mirroring the http_status codes the backend used.
export const badRequest = (detail?: unknown) => new HttpError(400, detail ?? statusPhrase(400));
export const unauthorized = (detail?: unknown) => new HttpError(401, detail ?? statusPhrase(401));
export const forbidden = (detail?: unknown) => new HttpError(403, detail ?? statusPhrase(403));
export const notFound = (detail?: unknown) => new HttpError(404, detail ?? statusPhrase(404));
export const conflict = (detail?: unknown) => new HttpError(409, detail ?? statusPhrase(409));
export const notAcceptable = (detail?: unknown) => new HttpError(406, detail ?? statusPhrase(406));
export const tooLarge = (detail?: unknown) => new HttpError(413, detail ?? statusPhrase(413));
export const tooManyRequests = (detail?: unknown) => new HttpError(429, detail ?? statusPhrase(429));

// ---- FastAPI request-validation errors ------------------------------------------
// FastAPI rejects malformed path/query/body input with 422 and a pydantic error list:
//   {"detail":[{"type":"int_parsing","loc":["path","post_id"],"msg":"...","input":"x"}]}
// The public blog page and the admin SPA read that shape, so the port reproduces the
// issue objects verbatim instead of inventing its own 400 bodies.
export interface ValidationIssue {
  type: string;
  loc: Array<string | number>;
  msg: string;
  input: unknown;
  ctx?: Record<string, unknown>;
}

export const unprocessable = (issues: ValidationIssue[] | ValidationIssue) =>
  new HttpError(422, Array.isArray(issues) ? issues : [issues]);

export type Loc = Array<string | number>;

const plural = (n: number, word: string) => `${word}${n === 1 ? '' : 's'}`;
const INT_MSG = 'Input should be a valid integer, unable to parse string as an integer';

export const missingIssue = (loc: Loc, input: unknown = null): ValidationIssue => ({
  type: 'missing',
  loc,
  msg: 'Field required',
  input,
});

export const enumIssue = (loc: Loc, input: unknown, values: readonly string[]): ValidationIssue => {
  // pydantic lists the accepted values as `'a', 'b' or 'c'` (Oxford-comma-free, and no
  // comma at all for a two-member enum).
  const quoted = values.map((v) => `'${v}'`);
  const expected =
    quoted.length <= 2
      ? quoted.join(' or ')
      : `${quoted.slice(0, -1).join(', ')} or ${quoted[quoted.length - 1]}`;
  return { type: 'enum', loc, msg: `Input should be ${expected}`, input, ctx: { expected } };
};

export const intIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'int_parsing',
  loc,
  msg: INT_MSG,
  input,
});

// pydantic distinguishes "wrong text" from "wrong kind of value": a null fed to a
// non-nullable int/bool/dict field reports the *_type variants.
export const intTypeIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'int_type',
  loc,
  msg: 'Input should be a valid integer',
  input,
});

export const boolTypeIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'bool_type',
  loc,
  msg: 'Input should be a valid boolean',
  input,
});

export const dictTypeIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'dict_type',
  loc,
  msg: 'Input should be a valid dictionary',
  input,
});

export const listIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'list_type',
  loc,
  msg: 'Input should be a valid list',
  input,
});

export const stringIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'string_type',
  loc,
  msg: 'Input should be a valid string',
  input,
});

export const tooShortIssue = (loc: Loc, input: string, min: number): ValidationIssue => ({
  type: 'string_too_short',
  loc,
  msg: `String should have at least ${min} ${plural(min, 'character')}`,
  input,
  ctx: { min_length: min },
});

export const tooLongIssue = (loc: Loc, input: string, max: number): ValidationIssue => ({
  type: 'string_too_long',
  loc,
  msg: `String should have at most ${max} ${plural(max, 'character')}`,
  input,
  ctx: { max_length: max },
});

// FastAPI reports a body that failed to decode as JSON (input arrives as an empty dict).
export const jsonInvalidIssue = (message: string): ValidationIssue => ({
  type: 'json_invalid',
  loc: ['body', 0],
  msg: 'JSON decode error',
  input: {},
  ctx: { error: message },
});

// Wrong HTTP method: FastAPI answers 405 + {"detail":"Method Not Allowed"} + an `allow` header.
export const methodNotAllowed = (allow: string) => {
  const error = new HttpError(405, 'Method Not Allowed');
  error.headers = { allow };
  return error;
};
