import { http } from '~/web/common';
import type { FileUploadVO, LoginRO } from '~/server/domain/types';

export const uploadFileAPI = async (formData: FormData) => {
  return await http.post<FileUploadVO>('/post/upload', formData);
};

export const loginAPI = async (loginRO: LoginRO) => {
  return await http.post('/login', loginRO).then(() => {});
};

export const logoutAPI = async () => {
  return await http.get('/logout').then(() => {});
};

export const infoAPI = async () => {
  return await http.get('/info');
};
