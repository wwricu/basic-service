// Mirrors wwricu/domain/enum.py — string-literal unions + const objects.
// Values must stay byte-identical: they are persisted in SQLite and exposed over the wire.

export const TagType = {
  POST_TAG: 'post_tag',
  POST_CAT: 'post_category',
} as const;
export type TagTypeEnum = (typeof TagType)[keyof typeof TagType];

export const PostStatus = {
  PUBLISHED: 'published',
  DRAFT: 'draft',
} as const;
export type PostStatusEnum = (typeof PostStatus)[keyof typeof PostStatus];

export const PostResourceType = {
  IMAGE: 'image',
  COVER_IMAGE: 'cover',
} as const;
export type PostResourceTypeEnum = (typeof PostResourceType)[keyof typeof PostResourceType];

export const RelationType = {
  POST_TAG: 'post_tag',
} as const;
export type RelationTypeEnum = (typeof RelationType)[keyof typeof RelationType];

export const DatabaseAction = {
  BACKUP: 'backup',
  RESTORE: 'restore',
  DOWNLOAD: 'download',
} as const;
export type DatabaseActionEnum = (typeof DatabaseAction)[keyof typeof DatabaseAction];

export const Environment = {
  DEVELOPMENT: 'dev',
  PRODUCTION: 'prod',
} as const;
export type EnvironmentEnum = (typeof Environment)[keyof typeof Environment];

export const ConfigKey = {
  ABOUT_CONTENT: 'about_content',
  TOTP_ENFORCE: 'totp_enforce',
  TOTP_SECRET: 'totp_secret',
  USERNAME: 'username',
  PASSWORD: 'password',
} as const;
export type ConfigKeyEnum = (typeof ConfigKey)[keyof typeof ConfigKey];

export const CacheKey = {
  POST_COUNT: 'post_count',
  CATEGORY_COUNT: 'category_count',
  TAG_COUNT: 'tag_count',
  STARTUP_TIMESTAMP: 'startup_timestamp',
  CONFIG: 'config:{key}',
  POST: 'post:{id}',
  ALL_POSTS: 'all_posts:{page_index}:{page_size}:{category}:{tag_list}',
  ALL_TAGS: 'all_tags:{type}',
  TOKEN_BUCKET: 'token_bucket:{name}:{id}',
} as const;

export const EntityType = {
  BLOG_POST: 'Post',
  POST_TAG: 'Tag',
  POST_CAT: 'Category',
  POST_IMAGE: 'Image',
  POST_COVER: 'Cover',
} as const;
export type EntityTypeEnum = (typeof EntityType)[keyof typeof EntityType];

export const TaskStatus = {
  RUNNING: 'running',
  SUCCESS: 'success',
  FAILED: 'failed',
} as const;
export type TaskStatusEnum = (typeof TaskStatus)[keyof typeof TaskStatus];

// Format a CacheKey template, mirroring Python str.format with the same placeholder names.
export function formatKey(template: string, vars: Record<string, string | number | null | undefined>): string {
  return template.replace(/\{(\w+)\}/g, (_, name) => {
    const v = vars[name];
    return v === undefined || v === null ? '' : String(v);
  });
}
