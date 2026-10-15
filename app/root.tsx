import { Links, Meta, Outlet, Scripts, ScrollRestoration } from 'react-router';
import { ConfigProvider, theme } from 'antd';
import { useEffect, useState } from 'react';
import type { PropsWithChildren } from 'react';
import '~/styles/App.css';

const { defaultAlgorithm, darkAlgorithm } = theme;

const lightTheme = {
  algorithm: defaultAlgorithm,
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
  },
  components: {
    Button: {
      colorPrimary: '#722ed1',
    },
    Layout: {
      headerBg: '#ffffff',
      headerHeight: '3',
      headerPadding: '0 5px',
    },
  },
};

const darkTheme = {
  algorithm: darkAlgorithm,
  components: {
    Layout: {
      headerHeight: '3',
      headerPadding: '0 5px',
    },
  },
};

export function useAutoTheme() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)');
    const update = () => setIsDark(query.matches);

    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  return isDark ? darkTheme : lightTheme;
}

export function Layout({ children }: PropsWithChildren) {
  return (
    <html lang='en'>
      <head>
        <meta charSet='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  const themeConfig = useAutoTheme();

  return (
    <ConfigProvider theme={themeConfig}>
      <Outlet />
    </ConfigProvider>
  );
}
