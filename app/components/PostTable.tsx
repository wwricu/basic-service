'use client';

import { useEffect, useState } from 'react';
import { Button, Flex, message, Popconfirm, Table, Tag, Tooltip, Typography } from 'antd';
import { deletePostAPI, getAllPost, updatePostStatusDetailAPI } from '~/web/api/post';
import { PostStatus } from '~/server/domain/enum';
import type { PostPreviewPageVO, PostPreviewVO, TagVO } from '~/server/domain/types';
import type { PostStatusEnum } from '~/server/domain/enum';

const { Column } = Table;

export default function AdminPostPage({ postStatus }: { postStatus: PostStatusEnum }) {
  const [list, setList] = useState<PostPreviewVO[]>([]);
  const [count, setCount] = useState<number>();
  const [pageIndex, setPageIndex] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const updatePostPage = (pageIndex: number = 1, pageSize: number = 10) => {
    setPageIndex(pageIndex);
    setPageSize(pageSize);
    getAllPost(pageIndex, pageSize, postStatus).then((res: PostPreviewPageVO) => {
      setList(res?.data);
      setCount(res?.count);
    });
  };

  const paginationProps = {
    showSizeChanger: true,
    showQuickJumper: false,
    pageSize: pageSize,
    current: pageIndex,
    total: count,
    onChange: updatePostPage,
  };

  useEffect(() => {
    document.title = `Admin - ${postStatus === PostStatus.PUBLISHED ? 'Published Posts' : 'Draft Posts'} - wwr.icu`;
    getAllPost(1, pageSize, postStatus).then((res: PostPreviewPageVO) => {
      setList(res?.data);
      setCount(res?.count);
    });
  }, [pageSize, postStatus]);

  return (
    <div>
      <Table<PostPreviewVO>
        size={'small'}
        scroll={{ x: true }}
        dataSource={list}
        rowKey={(postDetailVO: PostPreviewVO) => postDetailVO.id}
        pagination={paginationProps}
      >
        <Column<PostPreviewVO>
          title='Title'
          dataIndex='title'
          key='title'
          render={(_, { title }: PostPreviewVO) => (
            <Tooltip title={title}>
              <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</div>
            </Tooltip>
          )}
        />
        <Column<PostPreviewVO>
          title='Created time'
          dataIndex='create_time'
          key='create_time'
          ellipsis={true}
          width={100}
          render={(_, { create_time }: PostPreviewVO) => (
            <div style={{ whiteSpace: 'nowrap' }}>{create_time?.slice(0, 10)}</div>
          )}
        />
        <Column<PostPreviewVO>
          title='Category'
          dataIndex='category'
          key='category'
          width={150}
          render={(_, { category }: PostPreviewVO) =>
            category ? (
              <Tag style={{ maxWidth: 150, overflow: 'hidden' }} color={'blue'}>
                {category.name.toUpperCase()}
              </Tag>
            ) : (
              <></>
            )
          }
        />
        <Column<PostPreviewVO>
          title='Tags'
          dataIndex='tag_list'
          key='tag_list'
          render={(_, { tag_list }: PostPreviewVO) => (
            <>
              {tag_list.map((tag: TagVO) => {
                return (
                  <Tag style={{ overflow: 'hidden' }} color={'blue'} key={tag.id}>
                    {tag.name.toUpperCase()}
                  </Tag>
                );
              })}
            </>
          )}
        />
        <Column<PostPreviewVO>
          title='Action'
          key='action'
          width={180}
          render={(_, postDetailVO: PostPreviewVO) => (
            <Flex justify='space-evenly' gap={'small'}>
              <Typography.Link href={`/edit/${postDetailVO.id}`}>
                <Button size={'small'}>Edit</Button>
              </Typography.Link>
              <Popconfirm
                title={
                  postDetailVO.status === PostStatus.PUBLISHED
                    ? `Revoke "${postDetailVO.title}"`
                    : `Publish "${postDetailVO.title}"`
                }
                onConfirm={() => {
                  updatePostStatusDetailAPI(
                    postDetailVO.id,
                    postDetailVO.status === PostStatus.PUBLISHED ? PostStatus.DRAFT : PostStatus.PUBLISHED
                  ).then(() => {
                    message.success('success');
                    updatePostPage(pageIndex, pageSize);
                  });
                }}
              >
                <Button size={'small'}>{postDetailVO.status === PostStatus.PUBLISHED ? 'Revoke' : 'Publish'}</Button>
              </Popconfirm>
              {postDetailVO.status === PostStatus.PUBLISHED ? null : (
                <Popconfirm
                  title={`Delete ${postDetailVO.status} "${postDetailVO.title}"?`}
                  // Only rendered for non-published rows, so the danger branch of the
                  // original ternary was unreachable; keep the effective value.
                  okButtonProps={{ variant: 'solid', color: 'primary' }}
                  onConfirm={() =>
                    deletePostAPI(postDetailVO.id).then(() => {
                      message.success('success');
                      updatePostPage(pageIndex, pageSize);
                    })
                  }
                >
                  <Button variant='solid' color='danger' size='small'>
                    Delete
                  </Button>
                </Popconfirm>
              )}
            </Flex>
          )}
        />
      </Table>
    </div>
  );
}
