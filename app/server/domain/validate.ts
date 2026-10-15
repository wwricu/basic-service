// Pydantic-lax validation for the request objects the legacy FastAPI backend accepted.
//
// Every RO below was a pydantic model, so malformed input produced a 422 plus an issue
// list (`{"detail":[{"type":"int_parsing","loc":["body","page_index"],...}]}`) instead of
// a crash. The public blog page and the admin SPA both branch on that shape, so the port
// coerces the same values (bool → int, digit strings → int, everything else rejected) and
// emits byte-identical issue objects.
import {
  boolTypeIssue,
  dictTypeIssue,
  enumIssue,
  intIssue,
  intTypeIssue,
  jsonInvalidIssue,
  listIssue,
  missingIssue,
  stringIssue,
  unprocessable,
  type Loc,
  type ValidationIssue,
} from '~/server/lib/httpError';
import {
  ConfigKey,
  EntityType,
  PostResourceType,
  PostStatus,
  TagType,
  type PostResourceTypeEnum,
} from './enum';
import type {
  ConfigRO,
  LoginRO,
  PostRequestRO,
  PostUpdateRO,
  TagRequestRO,
  TagRO,
  TaskRunRO,
  TaskSearchRO,
  TrashBinRO,
  UserRO,
} from './types';

type Raw = Record<string, unknown>;

const isObject = (value: unknown): value is Raw =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const INT_STRING = /^[-+]?\d+$/;
const TRUE_WORDS = ['true', 'on', 'yes', '1'];
const FALSE_WORDS = ['false', 'off', 'no', '0'];

// ---- JSON body -------------------------------------------------------------

/**
 * Read the request body as a JSON object, mirroring FastAPI:
 *  - empty body       → 422 missing at ['body']
 *  - unparsable body  → 422 json_invalid ("Expecting value")
 *  - non-object body  → 422 model_attributes_type at ['body']
 */
export async function readJsonObject(request: Request): Promise<Raw> {
  const text = await request.text();
  if (text.trim() === '') throw unprocessable(missingIssue(['body'], null));
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw unprocessable(jsonInvalidIssue('Expecting value'));
  }
  if (!isObject(data)) {
    throw unprocessable({
      type: 'model_attributes_type',
      loc: ['body'],
      msg: 'Input should be a valid dictionary or object to extract fields from',
      input: data ?? null,
    });
  }
  return data;
}

// ---- field specs -----------------------------------------------------------

export type FieldSpec = {
  required?: boolean;
  default?: unknown;
  // `x: int | None = None` accepts an explicit null; `x: bool = False` does not
  // (pydantic answers with an `<base>_type` issue for null). Optional-by-default
  // legacy fields typed without `| None` — deleted, keyword, params — are the ones
  // that need this flag turned off explicitly.
  nullable?: boolean;
} & (
  | { type: 'int' }
  | { type: 'str'; max?: number }
  | { type: 'bool' }
  | { type: 'enum'; values: readonly string[] }
  | { type: 'strs' } // list[str]
  | { type: 'ints' } // list[int]
  | { type: 'dict' } // dict[str, Any]
);

/** Field name → spec, mirroring one pydantic model. */
export type RoSpec = Record<string, FieldSpec>;

/** Validate a body against a spec and hand it back typed as the legacy RO. */
export function parseRO<T>(body: Raw, spec: RoSpec): T {
  const issues: ValidationIssue[] = [];
  const out: Raw = {};
  for (const [key, field] of Object.entries(spec)) {
    const value = readField(body, key, field, issues);
    // Absent optional fields take the model's declared default, exactly as pydantic did;
    // an explicit null is kept as null (the models type those fields as `| None`).
    if (value === undefined) {
      if (field.default !== undefined) out[key] = field.default;
    } else {
      out[key] = value;
    }
  }
  if (issues.length) throw unprocessable(issues);
  return out as T;
}

function readField(
  body: Raw,
  key: string,
  field: FieldSpec,
  issues: ValidationIssue[],
): unknown {
  const value = body[key];
  const loc: Loc = ['body', key];

  if (value === undefined) {
    if (field.required) issues.push(missingIssue(loc, body));
    return undefined;
  }
  if (value === null) {
    // A `| None` annotation swallows null; a mandatory field or a plain-typed default
    // (`deleted: bool = False`) rejects it with the matching *_type issue.
    if (field.nullable ?? !field.required) return null;
    issues.push(nullIssue(loc, field));
    return undefined;
  }

  switch (field.type) {
    case 'int':
      return fromInt(value, loc, issues);
    case 'str':
      return fromStr(value, loc, issues, field.max);
    case 'bool':
      return fromBool(value, loc, issues);
    case 'enum':
      if (typeof value === 'string' && field.values.includes(value))
        return value;
      issues.push(enumIssue(loc, value, field.values));
      return undefined;
    case 'strs':
      return fromList(value, loc, issues, (item, itemLoc) =>
        fromStr(item, itemLoc, issues),
      );
    case 'ints':
      return fromList(value, loc, issues, (item, itemLoc) =>
        fromInt(item, itemLoc, issues),
      );
    case 'dict':
      if (isObject(value)) return value;
      issues.push(dictTypeIssue(loc, value));
      return undefined;
  }
}

// The issue pydantic raises for a null fed to a field that does not allow one.
function nullIssue(loc: Loc, field: FieldSpec): ValidationIssue {
  switch (field.type) {
    case 'int':
      return intTypeIssue(loc, null);
    case 'str':
      return stringIssue(loc, null);
    case 'bool':
      return boolTypeIssue(loc, null);
    case 'enum':
      return enumIssue(loc, null, field.values);
    case 'strs':
    case 'ints':
      return listIssue(loc, null);
    case 'dict':
      return dictTypeIssue(loc, null);
  }
}

// ---- scalar coercion (pydantic lax mode) ------------------------------------

function fromInt(
  value: unknown,
  loc: Loc,
  issues: ValidationIssue[],
): number | undefined {
  if (Number.isInteger(value)) return value as number;
  if (typeof value === 'boolean') return value ? 1 : 0; // pydantic lax: bool is an int
  if (typeof value === 'string' && INT_STRING.test(value.trim()))
    return Number(value.trim());
  if (typeof value === 'number' && Number.isFinite(value))
    return Math.trunc(value); // 1.0
  issues.push(intIssue(loc, value));
  return undefined;
}

function fromStr(
  value: unknown,
  loc: Loc,
  issues: ValidationIssue[],
  max?: number,
): string | undefined {
  if (typeof value !== 'string') {
    issues.push(stringIssue(loc, value));
    return undefined;
  }
  // StringConstraints counts code points, like Python's len().
  if (max !== undefined && Array.from(value).length > max) {
    issues.push({
      type: 'string_too_long',
      loc,
      msg: `String should have at most ${max} ${max === 1 ? 'character' : 'characters'}`,
      input: value,
      ctx: { max_length: max },
    });
    return undefined;
  }
  return value;
}

/** pydantic's lax bool words; undefined means "not a boolean". */
function parseBoolWord(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') return value;
  if (value === 0 || value === 1) return value === 1;
  if (typeof value === 'string') {
    const word = value.trim().toLowerCase();
    if (TRUE_WORDS.includes(word)) return true;
    if (FALSE_WORDS.includes(word)) return false;
  }
  return undefined;
}

const boolIssue = (loc: Loc, input: unknown): ValidationIssue => ({
  type: 'bool_parsing',
  loc,
  msg: 'Input should be a valid boolean, unable to interpret input',
  input,
});

function fromBool(
  value: unknown,
  loc: Loc,
  issues: ValidationIssue[],
): boolean | undefined {
  const parsed = parseBoolWord(value);
  if (parsed !== undefined) return parsed;
  issues.push(boolIssue(loc, value));
  return undefined;
}

function fromList(
  value: unknown,
  loc: Loc,
  issues: ValidationIssue[],
  item: (value: unknown, itemLoc: Loc) => unknown,
): unknown[] | undefined {
  if (!Array.isArray(value)) {
    issues.push(listIssue(loc, value));
    return undefined;
  }
  const out: unknown[] = [];
  value.forEach((entry, index) => {
    const parsed = item(entry, [...loc, index]);
    if (parsed !== undefined) out.push(parsed);
  });
  return out;
}

// ---- multipart form (POST /post/upload) ----------------------------------------

/**
 * FastAPI took the upload body as three form fields (`file: UploadFile`,
 * `post_id: int = Form()`, `file_type: PostResourceTypeEnum = Form()`) and answered a bad one
 * with the same 422 issue list, in declaration order. Form values arrive as strings, so unlike
 * the JSON bodies there is no bool/number coercion: only digits parse as an int, and a plain
 * text `file` part is a value_error instead of an upload.
 */
export interface UploadFormRO {
  file: File;
  post_id: number;
  file_type: PostResourceTypeEnum;
}

export function parseUploadFormRO(form: FormData): UploadFormRO {
  const issues: ValidationIssue[] = [];
  const file = formFile(form, 'file', issues);
  const postId = formInt(form, 'post_id', issues);
  const fileType = formEnum(form, 'file_type', postResourceValues, issues);
  if (issues.length) throw unprocessable(issues);
  return {
    file: file as File,
    post_id: postId as number,
    file_type: fileType as PostResourceTypeEnum,
  };
}

function formFile(
  form: FormData,
  key: string,
  issues: ValidationIssue[],
): File | undefined {
  const loc: Loc = ['body', key];
  const value = form.get(key);
  if (value === null) {
    issues.push(missingIssue(loc, null));
    return undefined;
  }
  if (value instanceof File) return value;
  // pydantic's value_error names the Python type it received and carries an empty error ctx.
  issues.push({
    type: 'value_error',
    loc,
    msg: `Value error, Expected UploadFile, received: <class '${pyTypeName(value)}'>`,
    input: value,
    ctx: { error: {} },
  });
  return undefined;
}

const PY_TYPE_NAMES: Record<string, string> = {
  string: 'str',
  number: 'float',
  boolean: 'bool',
  object: 'NoneType',
  undefined: 'NoneType',
};

const pyTypeName = (value: unknown): string =>
  typeof value === 'number' && Number.isInteger(value)
    ? 'int'
    : (PY_TYPE_NAMES[typeof value] ?? typeof value);

function formInt(
  form: FormData,
  key: string,
  issues: ValidationIssue[],
): number | undefined {
  const loc: Loc = ['body', key];
  const value = form.get(key);
  if (value === null) {
    issues.push(missingIssue(loc, null));
    return undefined;
  }
  if (typeof value === 'string' && INT_STRING.test(value.trim()))
    return Number(value.trim());
  issues.push(
    typeof value === 'string' ? intIssue(loc, value) : intTypeIssue(loc, value),
  );
  return undefined;
}

function formEnum(
  form: FormData,
  key: string,
  values: readonly string[],
  issues: ValidationIssue[],
): string | undefined {
  const loc: Loc = ['body', key];
  const value = form.get(key);
  if (value === null) {
    issues.push(missingIssue(loc, null));
    return undefined;
  }
  if (typeof value === 'string' && values.includes(value)) return value;
  issues.push(enumIssue(loc, value, values));
  return undefined;
}

// ---- request objects --------------------------------------------------------

const tagValues = Object.values(TagType);
const postStatusValues = Object.values(PostStatus);
const postResourceValues = Object.values(PostResourceType);

/**
 * One spec per legacy pydantic model (wwricu/domain/*.py).
 *
 * `nullable: false` marks the fields the models typed without `| None` even though they
 * carry a default (`deleted: bool = False`, `keyword: str = ''`, ...); null there is a 422.
 */
export const ROS = {
  postRequest: {
    page_index: { type: 'int', required: true },
    page_size: { type: 'int', required: true },
    tag_list: { type: 'strs' },
    category: { type: 'str' },
    status: { type: 'enum', values: postStatusValues },
    deleted: { type: 'bool', default: false, nullable: false },
  },
  postUpdate: {
    id: { type: 'int', required: true },
    title: { type: 'str', required: true },
    cover_id: { type: 'int' },
    preview: { type: 'str', required: true },
    status: { type: 'enum', values: postStatusValues, required: true },
    content: { type: 'str', required: true },
    tag_id_list: { type: 'ints', required: true },
    category_id: { type: 'int' },
  },
  // name is Annotated[str, StringConstraints(max_length=32)]
  tag: {
    id: { type: 'int' },
    name: { type: 'str', required: true, max: 32 },
    type: { type: 'enum', values: tagValues, default: TagType.POST_TAG },
  },
  tagRequest: {
    page_size: { type: 'int', default: 0 },
    page_index: { type: 'int', default: 0 },
    type: { type: 'enum', values: tagValues, default: TagType.POST_TAG },
  },
  config: {
    key: { type: 'enum', values: Object.values(ConfigKey), required: true },
    value: { type: 'str' },
  },
  user: {
    username: { type: 'str' },
    password: { type: 'str' },
    reset: { type: 'bool' },
  },
  trashBin: {
    id: { type: 'int', required: true },
    type: { type: 'enum', values: Object.values(EntityType), required: true },
    delete: { type: 'bool', default: false },
  },
  taskSearch: { keyword: { type: 'str', default: '', nullable: false } },
  taskRun: {
    name: { type: 'str', required: true },
    params: { type: 'dict', default: {}, nullable: false },
  },
  login: {
    username: { type: 'str', default: '', nullable: false },
    password: { type: 'str', default: '', nullable: false },
    totp: { type: 'str' },
  },
} satisfies Record<string, RoSpec>;

// Typed shorthands keep the call sites readable.
export const parsePostRequestRO = (body: Raw): PostRequestRO =>
  parseRO(body, ROS.postRequest);
export const parsePostUpdateRO = (body: Raw): PostUpdateRO =>
  parseRO(body, ROS.postUpdate);
export const parseTagRO = (body: Raw): TagRO => parseRO(body, ROS.tag);
export const parseTagRequestRO = (body: Raw): TagRequestRO =>
  parseRO(body, ROS.tagRequest);
export const parseConfigRO = (body: Raw): ConfigRO => parseRO(body, ROS.config);
export const parseUserRO = (body: Raw): UserRO => parseRO(body, ROS.user);
export const parseTrashBinRO = (body: Raw): TrashBinRO =>
  parseRO(body, ROS.trashBin);
export const parseTaskSearchRO = (body: Raw): TaskSearchRO =>
  parseRO(body, ROS.taskSearch);
export const parseTaskRunRO = (body: Raw): TaskRunRO =>
  parseRO(body, ROS.taskRun);
export const parseLoginRO = (body: Raw): LoginRO => parseRO(body, ROS.login);

// ---- path + query parameters -------------------------------------------------

/** `post_id: int` style path param: anything unparsable is FastAPI's 422 int_parsing. */
export function parsePathInt(raw: string | undefined, name: string): number {
  const value = raw ?? '';
  if (INT_STRING.test(value.trim())) return Number(value.trim());
  throw unprocessable(intIssue(['path', name], value));
}

/** Mandatory `str` query param. */
export function parseQueryStr(raw: string | null, name: string): string {
  if (raw === null) throw unprocessable(missingIssue(['query', name]));
  return raw;
}

/** Mandatory enum query param (`action: DatabaseActionEnum`, `key: ConfigKeyEnum`, ...). */
export function parseQueryEnum<T extends string>(
  raw: string | null,
  name: string,
  values: readonly T[],
): T {
  if (raw === null) throw unprocessable(missingIssue(['query', name]));
  if ((values as readonly string[]).includes(raw)) return raw as T;
  throw unprocessable(enumIssue(['query', name], raw, values));
}

/** Mandatory bool query param (`enforce: bool`). */
export function parseQueryBool(raw: string | null, name: string): boolean {
  if (raw === null) throw unprocessable(missingIssue(['query', name]));
  const parsed = parseBoolWord(raw);
  if (parsed !== undefined) return parsed;
  throw unprocessable(boolIssue(['query', name], raw));
}
