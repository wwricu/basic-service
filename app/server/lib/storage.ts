import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
  DeleteObjectCommand,
  DeleteObjectsCommand,
  ListObjectsV2Command,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { config, getS3Client, resourceDomain } from '~/server/lib/config';

// Mirrors wwricu/component/storage.py (AWSS3Storage).

export function resourceApi(): string {
  return `https://${resourceDomain()}/image/`;
}

function bucket(): string {
  return config().storage.bucket;
}

export async function storageGetObject(key: string): Promise<Buffer> {
  const res = await getS3Client().send(new GetObjectCommand({ Bucket: bucket(), Key: key }));
  const bytes = await res.Body?.transformToByteArray();
  if (!bytes) throw new Error(`S3 get empty body: ${key}`);
  return Buffer.from(bytes);
}

export async function storagePut(key: string, data: Uint8Array): Promise<string> {
  await getS3Client().send(new PutObjectCommand({ Bucket: bucket(), Key: key, Body: data }));
  return `${resourceApi()}${key}`;
}

export async function storageDelete(key: string): Promise<void> {
  await getS3Client().send(new DeleteObjectCommand({ Bucket: bucket(), Key: key }));
}

export async function storageBatchDelete(keys: string[]): Promise<void> {
  if (keys.length === 0) return;
  await getS3Client().send(
    new DeleteObjectsCommand({
      Bucket: bucket(),
      Delete: { Objects: keys.map((Key) => ({ Key })) },
    }),
  );
}

export async function storageListAll(): Promise<{ Key?: string; Size?: number }[]> {
  const res = await getS3Client().send(new ListObjectsV2Command({ Bucket: bucket() }));
  return (res.Contents ?? []) as { Key?: string; Size?: number }[];
}

export async function storagePresignUrl(key: string, expires: number): Promise<string> {
  return getSignedUrl(getS3Client(), new GetObjectCommand({ Bucket: bucket(), Key: key }), { expiresIn: expires });
}

// url -> key, or null when the url is not one of our managed resources (get_key_from_url).
export function getKeyFromUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  const api = resourceApi();
  const trimmed = url.trim();
  if (!trimmed.startsWith(api)) return null;
  return trimmed.slice(api.length);
}

// Used during database bootstrap (component/database.py init: download the db file if missing).
export async function storageEnsureFile(path: string): Promise<boolean> {
  try {
    const data = await storageGetObject(path);
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { writeFileSync } = require('node:fs') as typeof import('node:fs');
    writeFileSync(path, data);
    return true;
  } catch {
    return false;
  }
}

export function initStorageClient(): void {
  // Warm the S3 client so getS3Client() is ready; region/bucket come from config.
  getS3Client();
  void new S3Client({ region: config().storage.region });
}
