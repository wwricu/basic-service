'use client';

import React, { type ChangeEvent, useEffect, useState } from 'react';
import {
  BookOutlined,
  BorderlessTableOutlined,
  EditOutlined,
  TagsOutlined,
  MenuOutlined,
  DeleteOutlined,
  PlusOutlined,
  ExclamationCircleFilled,
  ScheduleOutlined,
} from '@ant-design/icons';
import { Button, Divider, Flex, Input, Menu, message, Modal, Popover } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router';
import { logoutAPI } from '~/web/api/common';
import { createPostAPI } from '~/web/api/post';
import { newTag } from '~/web/api/tag';
import { TagType } from '~/server/domain/enum';
import { useRefresh } from '~/web/common';
import type { PostDetailVO } from '~/server/domain/types';

const AdminMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeKey, setActiveKey] = useState<string>('');
  const [modalTitle, setModalTitle] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creatingName, setCreatingName] = useState<'category' | 'tag' | null>(null);
  const [inputValue, setInputValue] = useState<string>('');
  const [popoverOpen, setPopoverOpen] = useState(false);
  const refresh = useRefresh();

  useEffect(() => {
    setActiveKey(location.pathname.split('/').filter(Boolean)[0] || '');
  }, [location]);

  return (
    <Flex style={{ minHeight: '100vh', position: 'sticky', top: 0 }} vertical justify='space-between'>
      <Menu
        mode='inline'
        selectedKeys={[activeKey]}
        multiple={false}
        items={[
          {
            key: 'create',
            icon: <PlusOutlined />,
            label: 'Create',
            children: [
              {
                key: 'New Post',
                label: (
                  <Popover
                    trigger='click'
                    open={popoverOpen}
                    onOpenChange={setPopoverOpen}
                    content={
                      <div>
                        <div style={{ marginBottom: 8, height: 22 }}>
                          <ExclamationCircleFilled style={{ height: 22, width: 22, fontSize: 14, color: '#faad14' }} />
                          Create new post?
                        </div>
                        <div style={{ textAlign: 'end' }}>
                          <Button size='small' onClick={() => setPopoverOpen(false)}>
                            Cancel
                          </Button>
                          <Button
                            style={{ marginLeft: 8 }}
                            size='small'
                            type='primary'
                            onClick={() => {
                              createPostAPI().then((postDetailVO: PostDetailVO) => {
                                navigate(`/edit/${postDetailVO.id}`);
                                setPopoverOpen(false);
                                message.success('New post created');
                              });
                            }}
                          >
                            OK
                          </Button>
                        </div>
                      </div>
                    }
                  >
                    New Post
                  </Popover>
                ),
                onClick: () => {
                  if (!popoverOpen) {
                    // TODO: MUST check this or popover cannot be closed inline, but WHY?
                    setPopoverOpen(true);
                  }
                },
              },
              {
                key: 'New Category',
                label: 'New Category',
                onClick: () => {
                  setModalTitle('New Category');
                  setCreatingName('category');
                  setIsModalOpen(true);
                },
              },
              {
                key: 'New Tag',
                label: 'New Tag',
                onClick: () => {
                  setModalTitle('New Tag');
                  setCreatingName('tag');
                  setIsModalOpen(true);
                },
              },
            ],
          },
          {
            key: 'post',
            icon: <BookOutlined />,
            label: <Link to='/post'>Post</Link>,
          },
          {
            key: 'draft',
            icon: <EditOutlined />,
            label: <Link to='/draft'>Draft</Link>,
          },
          {
            key: 'category',
            icon: <BorderlessTableOutlined />,
            label: <Link to='/category'>Category</Link>,
          },
          {
            key: 'tag',
            icon: <TagsOutlined />,
            label: <Link to='/tag'>Tag</Link>,
          },
          {
            key: 'trash',
            icon: <DeleteOutlined />,
            label: <Link to='/trash'>Trash</Link>,
          },
          {
            key: 'management',
            icon: <MenuOutlined />,
            label: <Link to='/management'>Management</Link>,
          },
          {
            key: 'task',
            icon: <ScheduleOutlined />,
            label: <Link to='/task'>Task</Link>,
          },
        ]}
      />
      <Flex vertical justify='flex-end'>
        <Divider />
        <Button
          style={{ marginLeft: 16, marginRight: 16, marginBottom: 20 }}
          onClick={() => logoutAPI().then(() => navigate('/login'))}
        >
          Logout
        </Button>
      </Flex>
      <Modal
        title={modalTitle}
        closable={false}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          setModalTitle('');
        }}
        onOk={() => {
          if (!inputValue) {
            message.error('Please enter name');
            return;
          }
          const type = creatingName === 'category' ? TagType.POST_CAT : TagType.POST_TAG;
          newTag({ name: inputValue, type: type }).then(() => {
            setInputValue('');
            setIsModalOpen(false);
            message.success('success', 2);
            navigate(`/${creatingName}`);
            if (creatingName === activeKey) {
              refresh.triggerRefresh();
            }
            setModalTitle('');
          });
        }}
      >
        <Input
          value={inputValue}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            setInputValue(e.target.value);
          }}
          placeholder={`Input new ${creatingName} name`}
          style={{ marginTop: 12, marginBottom: 12 }}
        ></Input>
      </Modal>
    </Flex>
  );
};

export default AdminMenu;
