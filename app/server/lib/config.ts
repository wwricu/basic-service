import { existsSync, readFileSync } from 'node:fs';
import { S3Client } from '@aws-sdk/client-s3';
import { AppConfigDataClient, StartConfigurationSessionCommand, GetLatestConfigurationCommand } from '@aws-sdk/client-appconfigdata';
import { Environment, type EnvironmentEnum } from '~/server/domain/enum';
import { CommonConst } from '~/server/domain/constants';

export interface StorageConfig {
  region: string;
  bucket: string;
}

export interface DatabaseConfig {
  driver: string;
  username: string;
  password: string;
  host: string;
  port: number;
  database: string;
}

export interface SecurityConfig {
  username: string;
  password: string;
  secret_key: string;
  login_ip_times: number;
  login_ip_span: number;
  image_ip_qps: number;
  open_ip_qps: number;
}

export interface AppConfig {
  max_upload_size: number;
  storage: StorageConfig;
  database: DatabaseConfig;
  security: SecurityConfig;
}

export interface EnvVars {
  ENV: EnvironmentEnum;
  BASE_DOMAIN: string;
  ROOT_PATH: string;
  LOG_PATH: string;
  CONFIG_FILE: string;
  VERSION: string;
}

// Mirrors wwricu/config.py EnvironmentVariable defaults.
export const env: EnvVars = {
  ENV: (process.env.ENV as EnvironmentEnum) || Environment.DEVELOPMENT,
  BASE_DOMAIN: process.env.BASE_DOMAIN || 'wwr.icu',
  ROOT_PATH: process.env.ROOT_PATH || '/',
  LOG_PATH: process.env.LOG_PATH || 'logs',
  CONFIG_FILE: process.env.CONFIG_FILE || 'config.json',
  VERSION: process.env.VERSION || '0.0.1',
};

export function resourceDomain(): string {
  return `res.${env.BASE_DOMAIN}`;
}

// isDebug mirrors Python `__debug__` (true unless PYTHONOPTIMIZE is set).
// In Node we treat DEV environment as debug: it also enables the admin auth bypass the backend relies on.
export const isDebug = env.ENV === Environment.DEVELOPMENT;

function applyDefaults(raw: unknown): AppConfig {
  const r = raw as Partial<AppConfig> & Record<string, never>;
  const db = (r.database ?? {}) as Partial<DatabaseConfig>;
  const sec = (r.security ?? {}) as Partial<SecurityConfig>;
  const store = (r.storage ?? {}) as Partial<StorageConfig>;
  return {
    max_upload_size: r.max_upload_size ?? 10 * 1024 * 1024,
    storage: { region: store.region ?? 'us-west-2', bucket: store.bucket ?? '' },
    database: {
      driver: db.driver ?? 'sqlite',
      username: db.username ?? '',
      password: db.password ?? '',
      host: db.host ?? '',
      port: db.port ?? 0,
      database: db.database ?? '',
    },
    security: {
      username: sec.username ?? '',
      password: sec.password ?? '',
      secret_key: sec.secret_key ?? '',
      login_ip_times: sec.login_ip_times ?? 3,
      login_ip_span: sec.login_ip_span ?? 1800,
      image_ip_qps: sec.image_ip_qps ?? 0,
      open_ip_qps: sec.open_ip_qps ?? 0,
    },
  };
}

const AWS_REGION = 'us-west-2';
const CONFIG_PROFILE = 'config.json';

async function fetchFromAwsAppConfig(): Promise<AppConfig> {
  const client = new AppConfigDataClient({ region: AWS_REGION });
  const session = await client.send(
    new StartConfigurationSessionCommand({
      ApplicationIdentifier: CommonConst.APP_NAME,
      EnvironmentIdentifier: env.ENV,
      ConfigurationProfileIdentifier: CONFIG_PROFILE,
    }),
  );
  if (!session.InitialConfigurationToken) throw new Error('AppConfig: no initial token');
  const latest = await client.send(
    new GetLatestConfigurationCommand({ ConfigurationToken: session.InitialConfigurationToken }),
  );
  // GetLatestConfigurationResponse.Configuration is a Uint8Array (already buffered by the SDK).
  const bytes = latest.Configuration;
  if (!bytes) throw new Error('AppConfig: empty configuration');
  return applyDefaults(JSON.parse(Buffer.from(bytes).toString('utf-8')));
}

// Mirrors wwricu/config.py init_config(): prefer local file, else pull from AWS AppConfig.
export async function loadAppConfig(): Promise<AppConfig> {
  if (existsSync(env.CONFIG_FILE)) {
    return applyDefaults(JSON.parse(readFileSync(env.CONFIG_FILE, 'utf-8')));
  }
  return fetchFromAwsAppConfig();
}

export const appConfig: { current: AppConfig | null } = { current: null };

export function config(): AppConfig {
  if (!appConfig.current) throw new Error('app config not initialised');
  return appConfig.current;
}

// Lazily-created S3 client shared by the storage component (region from config at init time).
let s3Client: S3Client | null = null;
export function getS3Client(): S3Client {
  if (!s3Client) {
    s3Client = new S3Client({ region: config().storage.region || AWS_REGION });
  }
  return s3Client;
}
