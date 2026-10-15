'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Button, Flex, Input, message, Modal, Popconfirm, Table } from 'antd';
import type { InputRef } from 'antd';
import { useNavigate } from 'react-router';
import {
  databaseAPI,
  databaseDownloadURL,
  getConfigAPI,
  setConfigAPI,
  totpConfirmAPI,
  totpEnforceAPI,
  userAPI,
} from '~/web/api/manage';
import { ConfigKey, DatabaseAction } from '~/server/domain/enum';
import { AboutEditor } from './CKEditor';

const { Column } = Table;

type Action = {
  name: string;
  handle: () => void;
  confirmMessage?: string;
};

type ActionRow = {
  key: string;
  title: string | React.ReactNode;
  actions: Action[];
};

export default function ManagePage() {
  const [messageApi, messageContextHolder] = message.useMessage();

  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [aboutContent, setAboutContent] = useState<string>('');

  const inputRef = useRef<InputRef>(null);
  const navigate = useNavigate();

  const [username, setUsername] = useState<string>();
  const [totpEnforce, setTotpEnforce] = useState<boolean>(false);

  const [dynamicModal, setDynamicModal] = useState<{
    open: boolean;
    title: string;
    content: React.ReactNode;
    onOk: () => Promise<void>;
  } | null>(null);

  const getTotpEnforce = () => {
    getConfigAPI(ConfigKey.TOTP_ENFORCE).then((res: string | null) => {
      setTotpEnforce(!!res);
    });
  };

  useEffect(() => {
    document.title = 'Admin - Management - wwr.icu';
    getConfigAPI(ConfigKey.ABOUT_CONTENT).then((res: string | null) => {
      setAboutContent(res ?? '');
    });
    getConfigAPI(ConfigKey.USERNAME).then((res: string | null) => {
      setUsername(res ?? '');
    });
    getTotpEnforce();
  }, []);

  const actionTableData: ActionRow[] = [
    {
      key: 'about',
      title: 'About Page',
      actions: [
        {
          name: 'Edit',
          handle: () => {
            setIsAboutModalOpen(true);
          },
        },
      ],
    },
    {
      key: 'login',
      title: 'Login',
      actions: [
        {
          name: 'Set username',
          handle: () => {
            setDynamicModal({
              open: true,
              title: 'Set username',
              content: <Input ref={inputRef} defaultValue={username} style={{ marginTop: 12, marginBottom: 12 }} />,
              onOk: () => {
                const username = inputRef?.current?.input?.value;
                return new Promise<void>((resolve, reject) => {
                  if (!username) {
                    messageApi.error('Please input valid username');
                    reject();
                  } else {
                    userAPI({ username: username }).then(() => {
                      messageApi.success('success');
                      setDynamicModal(null);
                      resolve();
                      navigate('/login');
                    });
                  }
                });
              },
            });
          },
        },
        {
          name: 'Set password',
          handle: () => {
            setDynamicModal({
              open: true,
              title: 'Input new Password',
              content: (
                <Input.Password ref={inputRef} placeholder='New password' style={{ marginTop: 12, marginBottom: 12 }} />
              ),
              onOk: () => {
                const password = inputRef?.current?.input?.value;
                return new Promise<void>((resolve, reject) => {
                  if (!password) {
                    messageApi.error('Please input valid password');
                    reject();
                  } else {
                    userAPI({ password: password })
                      .then(() => {
                        messageApi.success('success');
                        setDynamicModal(null);
                        resolve();
                        navigate('/login');
                      })
                      .catch(() => reject());
                  }
                });
              },
            });
          },
        },
        {
          name: 'Reset all to default',
          handle: () => {
            userAPI({ reset: true }).then(() => {
              messageApi.success('success');
              navigate('/login');
            });
          },
          confirmMessage: 'Sure to reset username and password to default?',
        },
      ],
    },
    {
      key: 'database',
      title: 'Database',
      actions: [
        {
          name: 'Backup to cloud',
          handle: () => {
            databaseAPI(DatabaseAction.BACKUP).then(() => {
              messageApi.success('Database backup successfully.');
            });
          },
          confirmMessage: 'Sure to backup database? This will override cloud database',
        },
        {
          name: 'Restore from cloud',
          handle: () => {
            databaseAPI(DatabaseAction.RESTORE).then(() => {
              messageApi.success('Database restore successfully.');
            });
          },
          confirmMessage: 'Sure to restore database? This will override local database',
        },
        {
          name: 'Download to local',
          handle: () => {
            window.open(databaseDownloadURL(DatabaseAction.DOWNLOAD));
          },
          confirmMessage: 'Download database to local?',
        },
      ],
    },
    {
      key: 'totp',
      title: 'TOTP',
      actions: [
        {
          name: totpEnforce ? 'Disable TOTP' : 'Enforce TOTP',
          confirmMessage: totpEnforce ? 'Download database to local?' : undefined,
          handle: () => {
            if (totpEnforce) {
              totpEnforceAPI(false).then(getTotpEnforce).then(() => messageApi.success('success'));
              return;
            }
            totpEnforceAPI(true).then((secret) => {
              if (!secret) {
                messageApi.error('Failed to enforce totp');
                return;
              }
              setDynamicModal({
                open: true,
                title: secret,
                content: (
                  <Input
                    ref={inputRef}
                    placeholder='6-pin code from authenticator'
                    style={{ marginTop: 12, marginBottom: 12 }}
                  />
                ),
                onOk: () => {
                  return new Promise<void>((resolve, reject) => {
                    totpConfirmAPI(inputRef?.current?.input?.value ?? '')
                      .then(getTotpEnforce)
                      .then(() => {
                        messageApi.success('success');
                        setDynamicModal(null);
                        resolve();
                      })
                      .catch(() => reject());
                  });
                },
              });
            });
          },
        },
      ],
    },
  ];

  return (
    <>
      {messageContextHolder}
      {dynamicModal && (
        <Modal
          closable={false}
          open={dynamicModal.open}
          title={dynamicModal.title}
          onOk={dynamicModal.onOk}
          onCancel={() => setDynamicModal(null)}
          centered
        >
          {dynamicModal.content}
        </Modal>
      )}
      <Modal
        width={800}
        closable={false}
        open={isAboutModalOpen}
        onCancel={() => setIsAboutModalOpen(false)}
        onOk={() => {
          setConfigAPI({
            key: ConfigKey.ABOUT_CONTENT,
            value: aboutContent,
          }).then(() => {
            messageApi.success('success');
            setIsAboutModalOpen(false);
          });
        }}
        footer={[
          <span key={ConfigKey.ABOUT_CONTENT}>
            <Button onClick={() => setIsAboutModalOpen(false)}>Cancel</Button>
            <Button
              type='primary'
              style={{ marginLeft: 8 }}
              onClick={() => {
                setConfigAPI({
                  key: ConfigKey.ABOUT_CONTENT,
                  value: aboutContent,
                }).then(() => {
                  messageApi.success('success');
                  setIsAboutModalOpen(false);
                });
              }}
            >
              OK
            </Button>
          </span>,
        ]}
      >
        <AboutEditor content={aboutContent} setContent={(editorContent: string) => setAboutContent(editorContent)} />
      </Modal>
      <Table<ActionRow> scroll={{ x: true }} size='small' dataSource={actionTableData} pagination={false}>
        <Column<ActionRow> title='Name' dataIndex='title' key='title' ellipsis={true} />
        <Column<ActionRow>
          title='Actions'
          key='actions'
          render={(_, row: ActionRow) => (
            <Flex key={row.key} justify='flex-start' gap='middle'>
              {row?.actions.map((action: Action) =>
                action.confirmMessage ? (
                  <Popconfirm
                    key={action.name}
                    title={`Sure to ${action.name}?`}
                    onConfirm={action.handle}
                    okButtonProps={{ variant: 'solid', color: 'danger' }}
                  >
                    <Button size='small'>{action.name}</Button>
                  </Popconfirm>
                ) : (
                  <Button key={action.name} size='small' onClick={action.handle}>
                    {action.name}
                  </Button>
                )
              )}
            </Flex>
          )}
        />
      </Table>
    </>
  );
}
