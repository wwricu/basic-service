'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button, Card, Flex, Form, Input, InputNumber, message, Modal, Switch, Table, Tag } from 'antd';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { runningTaskAPI, runTaskAPI, searchTaskAPI } from '~/web/api/task';
import { TaskStatus } from '~/server/domain/enum';
import type { TaskInfoVO, TaskParamVO, TaskStateVO } from '~/server/domain/types';

const statusColor: Record<string, string> = {
  [TaskStatus.RUNNING]: 'processing',
  [TaskStatus.SUCCESS]: 'success',
  [TaskStatus.FAILED]: 'error',
};

const renderControl = (p: TaskParamVO) => {
  if (p.type === 'boolean') return <Switch />;
  if (p.type === 'integer' || p.type === 'number') return <InputNumber style={{ width: '100%' }} />;
  return <Input />;
};

export default function TaskPage() {
  const [keyword, setKeyword] = useState<string>('');
  const [tasks, setTasks] = useState<TaskInfoVO[]>([]);
  const [states, setStates] = useState<TaskStateVO[]>([]);

  const [current, setCurrent] = useState<TaskInfoVO | null>(null);
  const [isRunOpen, setIsRunOpen] = useState(false);
  const [form] = Form.useForm();

  const loadTasks = (kw: string) => searchTaskAPI(kw).then(setTasks);
  const loadStates = () => runningTaskAPI().then(setStates);

  useEffect(() => {
    document.title = 'Admin - Task - wwr.icu';
    loadTasks('');
    loadStates();
  }, []);

  const initialValues = useMemo(() => {
    const values: Record<string, unknown> = {};
    current?.params.forEach((p: TaskParamVO) => {
      if (p.default !== undefined && p.default !== null) values[p.name] = p.default;
    });
    return values;
  }, [current]);

  const openRunModal = (task: TaskInfoVO) => {
    setCurrent(task);
    setIsRunOpen(true);
  };

  const handleRun = async () => {
    if (!current) return;
    let params: Record<string, unknown> = {};
    if (current.params.length > 0) {
      try {
        params = await form.validateFields();
      } catch {
        return;
      }
    }
    await runTaskAPI({ name: current.name, params });
    message.success('任务已启动');
    setIsRunOpen(false);
    loadStates();
  };

  const taskColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: 'Params', key: 'params', render: (_: unknown, row: TaskInfoVO) => row.params.length },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, row: TaskInfoVO) => (
        <Button size='small' onClick={() => openRunModal(row)}>
          运行
        </Button>
      ),
    },
  ];

  const stateColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusColor[status] ?? 'default'}>{status}</Tag>,
    },
    {
      title: 'Output',
      key: 'output',
      render: (_: unknown, row: TaskStateVO) => (
        <pre style={{ whiteSpace: 'pre-wrap', margin: 0, maxHeight: 240, overflow: 'auto' }}>{row.output ?? ''}</pre>
      ),
    },
    {
      title: 'Error',
      key: 'error',
      render: (_: unknown, row: TaskStateVO) =>
        row.status === TaskStatus.FAILED ? (
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0, color: '#ff4d4f', maxHeight: 240, overflow: 'auto' }}>
            {row.error ?? ''}
          </pre>
        ) : null,
    },
  ];

  return (
    <Flex vertical gap='middle' style={{ padding: 16 }}>
      <Card>
        <Flex gap='small'>
          <Input
            value={keyword}
            placeholder='按任务名搜索'
            style={{ maxWidth: 280 }}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={() => loadTasks(keyword)}
          />
          <Button type='primary' icon={<SearchOutlined />} onClick={() => loadTasks(keyword)}>
            搜索
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadStates}>
            刷新
          </Button>
        </Flex>
      </Card>

      <Card title='任务'>
        <Table<TaskInfoVO>
          rowKey='name'
          size='small'
          columns={taskColumns}
          dataSource={tasks}
          pagination={false}
          scroll={{ x: true }}
        />
      </Card>

      <Card title='运行状态'>
        <Table<TaskStateVO>
          rowKey='run_id'
          size='small'
          columns={stateColumns}
          dataSource={states}
          pagination={false}
          scroll={{ x: true }}
        />
      </Card>

      <Modal
        title={current ? `运行 ${current.name}` : ''}
        open={isRunOpen}
        destroyOnClose
        onCancel={() => setIsRunOpen(false)}
        onOk={handleRun}
        okText='运行'
      >
        {current && current.params.length > 0 ? (
          <Form form={form} layout='vertical' initialValues={initialValues} preserve={false}>
            {current.params.map((p: TaskParamVO) => (
              <Form.Item
                key={p.name}
                label={p.name}
                name={p.name}
                valuePropName={p.type === 'boolean' ? 'checked' : 'value'}
                rules={p.required ? [{ required: true, message: `${p.name} 必填` }] : []}
              >
                {renderControl(p)}
              </Form.Item>
            ))}
          </Form>
        ) : (
          <div>确认运行该任务？</div>
        )}
      </Modal>
    </Flex>
  );
}
