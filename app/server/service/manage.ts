import bcrypt from 'bcryptjs';
import { authenticator } from 'otplib';
import { sysCache } from '~/server/lib/caches';
import * as confDb from '~/server/db/config';
import * as postDb from '~/server/db/post';
import * as tagDb from '~/server/db/tag';
import * as resDb from '~/server/db/resource';
import { badRequest, unauthorized } from '~/server/lib/httpError';
import { CacheKey, ConfigKey, formatKey, PostResourceType, TagType, type ConfigKeyEnum } from '~/server/domain/enum';
import { toIso } from '~/server/domain/datetime';
import { HttpErrorDetail } from '~/server/domain/constants';
import type { TrashBinVO, UserRO } from '~/server/domain/types';

// Match pyotp TOTP(secret).verify(totp, valid_window=1): accept the current and adjacent steps.
authenticator.options = { ...(authenticator.options ?? {}), window: 1 };

// Mirrors wwricu/service/manage.py.

export function verifyTotp(secret: string, totp: string): boolean {
  return authenticator.verify({ token: totp, secret });
}

export function setConfig(key: ConfigKeyEnum, value: string): void {
  if (typeof value !== 'string') throw badRequest();
  confDb.upsert(key, value);
  sysCache.delete(formatKey(CacheKey.CONFIG, { key }));
}

export function deleteConfig(keys: ConfigKeyEnum[]): void {
  confDb.remove(keys);
  for (const key of keys) sysCache.delete(formatKey(CacheKey.CONFIG, { key }));
}

export function getConfig(key: ConfigKeyEnum): string | null {
  const cacheKey = formatKey(CacheKey.CONFIG, { key });
  const cached = sysCache.get<string>(cacheKey);
  if (cached !== null && cached !== undefined) return cached;
  const value = confDb.getConf(key);
  if (value !== null) sysCache.set(cacheKey, value);
  return value;
}

export function listTrash(): TrashBinVO[] {
  const result: TrashBinVO[] = [];

  for (const post of postDb.findByCriteria({ deleted: true })) {
    result.push({
      id: post.id,
      name: post.title,
      info: post.preview,
      type: EntityTypeOf.BLOG_POST,
      delete_time: toIso(post.update_time) ?? post.update_time,
    });
  }

  for (const tag of tagDb.findByCriteria({ deleted: true })) {
    result.push({
      id: tag.id,
      name: tag.name,
      type: tag.type === TagType.POST_TAG ? EntityTypeOf.POST_TAG : EntityTypeOf.POST_CAT,
      delete_time: toIso(tag.update_time) ?? tag.update_time,
    });
  }

  for (const res of resDb.findDeleted()) {
    result.push({
      id: res.id,
      name: res.name ?? '',
      info: res.url,
      type: res.type === PostResourceType.IMAGE ? EntityTypeOf.POST_IMAGE : EntityTypeOf.POST_COVER,
      delete_time: toIso(res.update_time) ?? res.update_time,
    });
  }

  result.sort((a, b) => (a.delete_time < b.delete_time ? 1 : a.delete_time > b.delete_time ? -1 : 0));
  return result;
}

// Local alias keeps the EntityType import out of the value namespace clash.
import { EntityType as EntityTypeOf } from '~/server/domain/enum';

export async function updateAdminUser(user: UserRO): Promise<void> {
  if (user.username != null) {
    if (user.username.length < 4 || !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(user.username)) {
      throw badRequest('Invalid username');
    }
    setConfig(ConfigKey.USERNAME, user.username);
  }

  if (user.password != null) {
    const isAlnum = user.password.length > 0 && /^[a-zA-Z0-9]+$/.test(user.password);
    if (user.password.length < 8 || isAlnum) {
      throw badRequest('Invalid password');
    }
    // bcrypt.hashpw(pw, gensalt()) then base64-encode the resulting hash string (Python parity).
    const credential = await bcrypt.hash(user.password, 12);
    setConfig(ConfigKey.PASSWORD, Buffer.from(credential, 'utf-8').toString('base64'));
  }

  if (user.reset) deleteConfig([ConfigKey.USERNAME, ConfigKey.PASSWORD]);
}

export function enforceTotp(enforce: boolean): string | null {
  if (!enforce) {
    deleteConfig([ConfigKey.TOTP_ENFORCE, ConfigKey.TOTP_SECRET]);
    return null;
  }
  const secret = authenticator.generateSecret(); // base32, like pyotp.random_base32()
  setConfig(ConfigKey.TOTP_SECRET, secret);
  return secret;
}

export function confirmTotp(totp: string): void {
  const secret = getConfig(ConfigKey.TOTP_SECRET);
  if (secret === null) throw badRequest();
  if (!verifyTotp(secret, totp)) throw unauthorized(HttpErrorDetail.WRONG_TOTP);
  setConfig(ConfigKey.TOTP_ENFORCE, String(true));
}

export { HttpErrorDetail };
