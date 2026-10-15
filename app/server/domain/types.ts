import type {
  ConfigKeyEnum,
  EntityTypeEnum,
  PostResourceTypeEnum,
  PostStatusEnum,
  RelationTypeEnum,
  TagTypeEnum,
  TaskStatusEnum,
} from './enum';

// ---- DB row shapes (mirror wwricu/domain/entity.py columns) ----

export interface Timestamped {
  id: number;
  deleted: number; // SQLite stores BOOLEAN as 0/1
  create_time: string;
  update_time: string;
}

export interface BlogPostRow extends Timestamped {
  title: string;
  cover_id: number | null;
  content: string;
  preview: string;
  status: string;
  category_id: number | null;
}

export interface PostTagRow extends Timestamped {
  name: string;
  type: string;
  count: number;
}

export interface EntityRelationRow extends Timestamped {
  src_id: number;
  dst_id: number;
  type: string;
}

export interface PostResourceRow extends Timestamped {
  post_id: number;
  name: string | null;
  key: string;
  type: string | null;
  url: string | null;
}

export interface SysConfigRow extends Timestamped {
  key: string;
  value: string | null;
}

// FTS5 external-content-style table; `id` is an ordinary column (see migration).
export interface BlogPostSearchRow {
  id: number;
  title: string;
  preview: string;
  search_content: string;
}

// ---- Common RO/VO (mirror wwricu/domain/common.py) ----

export interface LoginRO {
  username?: string;
  password?: string;
  totp?: string | null;
}

export interface UserRO {
  username?: string | null;
  password?: string | null;
  reset?: boolean | null;
}

export interface ConfigRO {
  key: ConfigKeyEnum;
  value?: string | null;
}

export interface PageVO<T> {
  page_index: number | null;
  page_size: number | null;
  count: number;
  data: T[];
}

export type PostPreviewPageVO = PageVO<PostPreviewVO>;

export interface FileUploadVO {
  id: number;
  name: string | null;
  key: string;
  location: string;
}

export interface AboutPageVO {
  content: string | null;
  post_count: number;
  category_count: number;
  tag_count: number;
  startup_timestamp: number;
}

export interface TrashBinRO {
  id: number;
  type: EntityTypeEnum;
  delete?: boolean | null;
}

export interface TrashBinVO {
  id: number;
  name: string;
  info?: string | null;
  type: EntityTypeEnum;
  delete_time: string;
}

export interface LoginVO {
  detail?: string | null;
}

export interface TokenBucketState {
  tokens: number;
  updated_at: number;
}

// ---- Tag (mirror wwricu/domain/tag.py) ----

export interface TagRO {
  id?: number | null;
  name: string;
  type?: TagTypeEnum | null;
}

export interface TagRequestRO {
  page_size?: number | null;
  page_index?: number | null;
  type?: TagTypeEnum | null;
}

export interface TagQueryDTO {
  tag_ids?: number[] | null;
  name?: string | null;
  type?: TagTypeEnum | null;
  deleted?: boolean | null;
  page_index?: number | null;
  page_size?: number | null;
}

export interface TagVO {
  id: number;
  name: string;
  type: TagTypeEnum;
  count: number | null;
}

export interface TagUpdateDTO {
  tag_id_list: number[];
  category_id: number | null;
  status: PostStatusEnum;
}

// ---- Post (mirror wwricu/domain/post.py) ----

export interface PostRequestRO {
  page_index: number;
  page_size: number;
  tag_list?: string[] | null;
  category?: string | null;
  status?: PostStatusEnum | null;
  deleted?: boolean;
}

export interface PostUpdateRO {
  id: number;
  title: string;
  cover_id?: number | null;
  preview: string;
  status: PostStatusEnum;
  content: string;
  tag_id_list: number[];
  category_id?: number | null;
}

export interface PostResourceVO {
  id: number;
  name: string | null;
  key: string;
  url: string;
  type: PostResourceTypeEnum;
}

export interface PostPreviewVO {
  id: number;
  title: string | null;
  cover?: PostResourceVO | null;
  preview: string;
  tags?: TagVO[] | null;
  tag_list: TagVO[];
  category?: TagVO | null;
  status?: PostStatusEnum | null;
  create_time?: string | null;
  update_time?: string | null;
}

export interface PostDetailVO extends PostPreviewVO {
  content: string;
}

export interface PostSearchVO extends PostPreviewVO {
  snippet?: string | null;
}

export interface PostQueryDTO {
  post_ids?: number[] | null;
  category_id?: number | null;
  deleted?: boolean | null;
  status?: PostStatusEnum | null;
  page_index?: number | null;
  page_size?: number | null;
}

// ---- Task (mirror wwricu/domain/task.py) ----

export interface TaskParamVO {
  name: string;
  type: string;
  required: boolean;
  default?: unknown;
}

export interface TaskInfoDTO {
  name: string;
  params: TaskParamVO[];
}

// Alias for frontend compatibility
export type TaskInfoVO = TaskInfoDTO;

export interface TaskSearchRO {
  keyword?: string;
}

export interface TaskRunRO {
  name: string;
  params?: Record<string, unknown>;
}

export interface TaskRunVO {
  run_id: string;
  name: string;
  status: TaskStatusEnum;
}

export interface TaskStateVO {
  run_id: string;
  name: string;
  status: TaskStatusEnum;
  output?: string | null;
  error?: string | null;
}

export type { RelationTypeEnum };
