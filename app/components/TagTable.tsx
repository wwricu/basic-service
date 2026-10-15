'use client';

import React, { useEffect, useState } from 'react';
import { Button, message, Space } from 'antd';
import type { TableProps } from 'antd';
import { Form, Input, InputNumber, Popconfirm, Table } from 'antd';
import { deleteTag, getAllTag, updateTag } from '~/web/api/tag';
import { TagType } from '~/server/domain/enum';
import type { TagVO } from '~/server/domain/types';
import type { TagTypeEnum } from '~/server/domain/enum';
import { useRefresh } from '~/web/common';

interface EditableCellProps extends React.HTMLAttributes<HTMLElement> {
  editing: boolean;
  dataIndex: string;
  title: string;
  inputType: 'number' | 'text';
  record: TagVO;
  index: number;
}

const EditableCell: React.FC<React.PropsWithChildren<EditableCellProps>> = ({
  editing,
  dataIndex,
  title,
  inputType,
  children,
  ...restProps
}) => {
  const inputNode = inputType === 'number' ? <InputNumber /> : <Input />;

  return (
    <td {...restProps}>
      {editing ? (
        <Form.Item style={{ margin: 0 }} name={dataIndex} rules={[{ required: true, message: `Please Input ${title}!` }]}>
          {inputNode}
        </Form.Item>
      ) : (
        children
      )}
    </td>
  );
};

export default function TagTable({ tagType }: { tagType: TagTypeEnum }) {
  const [form] = Form.useForm();
  const [data, setData] = useState<TagVO[]>([]);
  const [editingKey, setEditingKey] = useState<number | undefined>();
  const isEditing = (tag: TagVO) => tag.id === editingKey;
  const [messageApi, contextHolder] = message.useMessage();
  const refresh = useRefresh();

  useEffect(() => {
    document.title = `Admin - ${tagType === TagType.POST_CAT ? 'Post Categories' : 'Post Tags'} - wwr.icu`;
    getAllTag(tagType).then((tagList: TagVO[]) => {
      setData(tagList);
    });
    setEditingKey(undefined);
  }, [tagType, refresh.key]);

  const edit = (tag: Partial<TagVO> & { id: React.Key }) => {
    form.setFieldsValue({ name: '', ...tag });
    setEditingKey(tag.id as number);
  };

  const cancel = () => {
    setEditingKey(undefined);
  };

  const remove = (tag: TagVO) => {
    deleteTag(tag.id).then(() => {
      const newData = [...data];
      const index = newData.findIndex((item) => tag.id === item.id);
      newData.splice(index, 1);
      setData(newData);
      messageApi.success('success');
    });
  };

  const save = async (tagId: number) => {
    try {
      const row = (await form.validateFields()) as TagVO;

      const newData = [...data];
      const index = newData.findIndex((item) => tagId === item.id);
      if (index < 0) {
        return;
      }
      const tag = newData[index];
      updateTag({ ...tag, ...row }).then((tagVO) => {
        newData.splice(index, 1, tagVO);
        setData(newData);
        messageApi.success('success');
      });
      setEditingKey(undefined);
    } catch (errInfo) {
      console.log('Validate Failed:', errInfo);
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      width: '40%',
      editable: true,
    },
    {
      title: 'Count',
      dataIndex: 'count',
      width: '30%',
      editable: false,
    },
    {
      width: '30%',
      title: 'Action',
      dataIndex: 'Action',
      render: (_: unknown, tag: TagVO) => {
        return isEditing(tag) ? (
          <Space size='middle'>
            <Popconfirm title={`Save ${tag.name}?`} onConfirm={() => save(tag.id)}>
              <Button variant='outlined' color='primary' size='small'>
                Save
              </Button>
            </Popconfirm>
            <Button size='small' onClick={cancel}>
              Cancel
            </Button>
          </Space>
        ) : (
          <Space size='middle'>
            <Button size='small' disabled={editingKey !== undefined} onClick={() => edit(tag)}>
              Edit
            </Button>
            <Popconfirm title={`Delete ${tag.name}?`} disabled={editingKey !== undefined} onConfirm={() => remove(tag)}>
              <Button variant={editingKey !== undefined ? 'outlined' : 'solid'} size='small' color='danger'>
                Delete
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  const mergedColumns: TableProps<TagVO>['columns'] = columns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record: TagVO) => ({
        record,
        inputType: 'text',
        dataIndex: col.dataIndex,
        title: col.title,
        editing: isEditing(record),
      }),
    };
  });

  return (
    <>
      {contextHolder}
      <Form form={form} component={false}>
        <Table<TagVO>
          size={'small'}
          scroll={{ x: true }}
          rowKey={(tagVO: TagVO) => tagVO.id}
          components={{ body: { cell: EditableCell } }}
          bordered
          dataSource={data}
          columns={mergedColumns}
          rowClassName='editable-row'
          pagination={{ onChange: cancel, simple: true }}
        />
      </Form>
    </>
  );
}
