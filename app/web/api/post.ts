import type { PostDetailVO, PostPreviewPageVO, PostRequestRO, PostUpdateRO } from '~/server/domain/types';
import type { PostStatusEnum } from '~/server/domain/enum';
import { http } from '~/web/common';

export const getAllPost = async (pageIndex: number, pageSize: number, status: PostStatusEnum) => {
  const postRequest: PostRequestRO = {
    page_index: pageIndex,
    page_size: pageSize,
    status: status,
  };
  return await http.post<PostPreviewPageVO>('/post/all', postRequest);
};

export const createPostAPI = async () => {
  return await http.get<PostDetailVO>('/post/create');
};

export const getPostDetailAPI = async (postId: string | number) => {
  return await http.get<PostDetailVO>(`/post/detail/${postId}`);
};

export const updatePostDetailAPI = async (postUpdateRO: PostUpdateRO) => {
  return await http.post<PostDetailVO>('/post/update', postUpdateRO);
};

export const updatePostStatusDetailAPI = async (postId: number, postStatusEnum: PostStatusEnum) => {
  return await http.get<void>(`/post/status/${postId}?status=${postStatusEnum}`);
};

export const deletePostAPI = async (postId: string | number) => {
  return await http.get(`/post/delete/${postId}`).then(() => {});
};
