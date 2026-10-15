// Mirrors wwricu/domain/constant.py
export const HttpErrorDetail = {
  POST_NOT_FOUND: 'Post Not Found',
  WRONG_PASSWORD: 'Wrong Username or Password',
  WRONG_TOTP: 'Wrong TOTP',
  NEED_TOTP: 'Please input TOTP',
} as const;

export const CommonConst = {
  SESSION_ID_2FA: '2fa_session_id',
  SESSION_ID: 'session_id',
  COOKIE_SIGN: 'sign',
  APP_NAME: 'wwr.icu',
  IMG_TAG: 'img',
  SRC_PROP: 'src',
  IMAGE_IP_BUCKET: 'image:{ip}',
  OPEN_IP_BUCKET: 'open:{ip}',
  TOKEN_SEPARATOR: '\x01',
  MARK_BEGIN: '<mark>',
  MARK_END: '</mark>',
} as const;

export const TimeConst = {
  COOKIE_MAX_AGE: 7 * 24 * 60 * 60,
  ONE_DAY_SECONDS: 60 * 60 * 24,
  TOTP_EXPIRATION: 300,
  CACHE_EXPIRATION: 600,
} as const;
