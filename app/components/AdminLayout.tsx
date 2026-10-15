import { Button, Drawer, Flex, Layout, Spin } from 'antd';
import Sider from 'antd/es/layout/Sider';
import { Content, Header } from 'antd/es/layout/layout';
import { Outlet, useLocation } from 'react-router';
import React, { Suspense, useState } from 'react';
import { MenuOutlined } from '@ant-design/icons';
import { RefreshContext } from '~/web/common';

const LazyMenu = React.lazy(() => import('~/components/AdminMenu'));

const RefreshProvider = ({
  value,
  children,
}: {
  value: { key: boolean; triggerRefresh: () => void };
  children: React.ReactNode;
}) => <RefreshContext.Provider value={value}>{children}</RefreshContext.Provider>;

const Loading: React.FC = () => {
  return (
    <Spin style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} size='large' />
  );
};

// Pathless layout route: mirrors the legacy SPA AppLayout (mobile header + desktop sider
// + drawer), and owns the RefreshContext the tables use to re-query after a mutation.
export default function AdminLayout() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(false);

  const getPosition = () => {
    const url = location.pathname.split('/').filter(Boolean)[0] || null;
    if (!url) {
      return null;
    }
    return url[0].toUpperCase() + url.slice(1);
  };

  return (
    <RefreshProvider value={{ key: refreshKey, triggerRefresh: () => setRefreshKey((prev) => !prev) }}>
      <Layout style={{ height: '100vh' }}>
        <Header className='lg:hidden'>
          <Flex align='center' gap='small'>
            <Button color='default' variant='text' onClick={() => setOpen(true)}>
              <MenuOutlined />
            </Button>
            <span style={{ verticalAlign: 'middle' }}>{getPosition()}</span>
          </Flex>
        </Header>
        <Layout>
          <Sider className='max-lg:hidden' theme='light'>
            <Suspense fallback={<Loading />}>
              <LazyMenu />
            </Suspense>
          </Sider>
          <Content>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
      <Drawer
        width={200}
        title={null}
        placement='left'
        closable={false}
        onClose={() => setOpen(false)}
        open={open}
        key={'left'}
        styles={{ body: { padding: 0 } }}
      >
        <Suspense fallback={<Loading />}>
          <LazyMenu />
        </Suspense>
      </Drawer>
    </RefreshProvider>
  );
}
