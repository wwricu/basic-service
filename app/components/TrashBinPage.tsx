'use client';

import React, { useEffect, useState } from 'react';
import { Button, message, Popconfirm, Space, Table, Tooltip } from 'antd';
import { trashEditAPI, trashGetAllAPI } from '~/web/api/manage';
import { EntityType } from '~/server/domain/enum';
import type { TrashBinVO } from '~/server/domain/types';

const { Column } = Table;

const TrashBinPage: React.FC = () => {
  const [messageApi, messageContextHolder] = message.useMessage();
  const [trashBinVOList, setTrashBinVOList] = useState<TrashBinVO[]>([]);

  const getAllTrashBinVO = () => {
    trashGetAllAPI().then((data: TrashBinVO[]) => {
      setTrashBinVOList(data);
    });
  };

  useEffect(() => {
    getAllTrashBinVO();
  }, []);

  return (
    <>
      {messageContextHolder}
      <Table<TrashBinVO>
        scroll={{ x: true }}
        dataSource={trashBinVOList}
        rowKey={(trashBinVO: TrashBinVO) => `${trashBinVO.id}:${trashBinVO.type}`}
      >
        <Column<TrashBinVO>
          title='Name'
          dataIndex='name'
          key='name'
          render={(_, { name }: TrashBinVO) => (
            <Tooltip title={name}>
              <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{name}</div>
            </Tooltip>
          )}
        />
        <Column<TrashBinVO> title='Type' dataIndex='type' key='type' width={100} />
        <Column<TrashBinVO>
          title='Info'
          dataIndex='info'
          key='info'
          render={(_, { info }: TrashBinVO) => (
            <Tooltip title={info}>
              <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{info}</div>
            </Tooltip>
          )}
        />
        <Column<TrashBinVO>
          title='Delete time'
          dataIndex='delete_time'
          ellipsis={true}
          key='delete_time'
          width={100}
          render={(_, { delete_time }: TrashBinVO) => <div style={{ whiteSpace: 'nowrap' }}>{delete_time.slice(0, 10)}</div>}
        />
        <Column<TrashBinVO>
          title='Action'
          key='action'
          width={160}
          render={(_, trashBinVO: TrashBinVO) => (
            <Space size='middle'>
              <Popconfirm
                title={`Recover ${trashBinVO.type} "${trashBinVO.name}"?`}
                onConfirm={() => {
                  trashEditAPI({
                    id: trashBinVO.id,
                    type: trashBinVO.type,
                    delete: false,
                  }).then(() => {
                    messageApi.success(`${trashBinVO.type} ${trashBinVO.name} recovered`);
                    getAllTrashBinVO();
                  });
                }}
              >
                <Button
                  variant='outlined'
                  size='small'
                  color='primary'
                  disabled={trashBinVO.type === EntityType.POST_COVER || trashBinVO.type === EntityType.POST_IMAGE}
                >
                  Recover
                </Button>
              </Popconfirm>
              <Popconfirm
                title={`Delete ${trashBinVO.type} "${trashBinVO.name}"?`}
                okButtonProps={{ variant: 'solid', color: 'danger' }}
                onConfirm={() =>
                  trashEditAPI({
                    id: trashBinVO.id,
                    type: trashBinVO.type,
                    delete: true,
                  }).then(() => {
                    messageApi.success(`${trashBinVO.type} ${trashBinVO.name} deleted`);
                    getAllTrashBinVO();
                  })
                }
              >
                <Button variant='solid' size='small' color='danger'>
                  Delete
                </Button>
              </Popconfirm>
            </Space>
          )}
        />
      </Table>
    </>
  );
};

export default TrashBinPage;
