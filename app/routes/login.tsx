import { infoAPI, loginAPI } from '~/web/api/common';
import { useEffect, useState } from 'react';
import { Form, Button, Input, message, Flex } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router';
import { HttpError } from '~/web/common';
import type { LoginRO } from '~/server/domain/types';
import icon from '/doge.png';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loginForm] = Form.useForm();
  const [loginPhase, setLoginPhase] = useState<'account' | 'totp'>('account');

  useEffect(() => {
    document.title = 'Admin - Login - wwr.icu';
    if (import.meta.env.PROD) {
      infoAPI().then(
        () =>
          message.success('Logging in...', 1).then(() => navigate('/'))
      );
    }
  }, [location.pathname, navigate]);

  return (
    <Flex justify='center' style={{ height: '100vh' }}>
      <Form
        style={{ width: 328, marginTop: 24 }}
        form={loginForm}
        onValuesChange={(changedValues, allValues) => {
          if (changedValues.totp !== undefined && allValues.totp?.length === 6) {
            loginForm.submit();
          }
        }}
        onFinish={(record: Record<string, string>) =>
          loginAPI({ username: record.username, password: record.password, totp: record.totp })
            .then(() => navigate('/'))
            .catch((err: HttpError) => {
              loginForm.setFieldsValue({ totp: '' });
              if (err.status === 401 && err.message === 'Please input TOTP') {
                setLoginPhase('totp');
                return;
              }
              throw err;
            })
        }
      >
        <Flex justify='center' align='center' gap='middle' style={{ height: 80, width: '100%' }}>
          <img alt='icon' src={icon} width={44} height={44} />
          <p style={{ fontSize: 36, fontWeight: 500 }}>wwr.icu</p>
        </Flex>
        <div style={loginPhase === 'account' ? {} : { display: 'none' }}>
          <Form.Item<LoginRO> name='username' rules={[{ required: true, message: 'Please input your username!' }]}>
            <Input allowClear size='large' prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item<LoginRO> name='password' rules={[{ required: true, message: 'Please input your password!' }]}>
            <Input.Password size='large' prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item>
            <Button block size='large' type='primary' htmlType='submit'>
              Login
            </Button>
          </Form.Item>
        </div>
        <Flex justify='center'>
          {/* Flex to work around with mobile safari; TODO: Fix OTP width on safari */}
          <Form.Item<LoginRO> name='totp' style={loginPhase === 'totp' ? {} : { display: 'none' }}>
            <Input.OTP size='large' />
          </Form.Item>
        </Flex>
      </Form>
    </Flex>
  );
}
