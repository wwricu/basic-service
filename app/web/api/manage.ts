import type { ConfigRO, TrashBinRO, TrashBinVO, UserRO } from '~/server/domain/types';
import type { ConfigKeyEnum, DatabaseActionEnum } from '~/server/domain/enum';
import { http } from '~/web/common';

export const databaseAPI = async (action: DatabaseActionEnum) => {
  return await http.get(`/manage/database?action=${action}`).then(() => {});
};

export const databaseDownloadURL = (action: DatabaseActionEnum) => `/api/manage/database?action=${action}`;

export const setConfigAPI = async (config: ConfigRO) => {
  return await http.post('/manage/config/set', config).then(() => {});
};

export const getConfigAPI = async (key: ConfigKeyEnum) => {
  return await http.get<string | null>(`/manage/config/get?key=${key}`);
};

export const userAPI = async (userRO: UserRO) => {
  return await http.post('/manage/user', userRO).then(() => {});
};

export const trashGetAllAPI = async () => {
  return await http.get<TrashBinVO[]>('/manage/trash/all');
};

export const trashEditAPI = async (trashBinRO: TrashBinRO) => {
  return await http.post('/manage/trash/edit', trashBinRO).then(() => {});
};

export const totpEnforceAPI = async (enforce: boolean) => {
  return await http.get<string | null>(`/manage/totp/enforce?enforce=${enforce}`);
};

export const totpConfirmAPI = async (totp: string) => {
  return await http.get(`/manage/totp/confirm?totp=${totp}`).then(() => {});
};
