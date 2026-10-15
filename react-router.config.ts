import type { Config } from '@react-router/dev/config';

export default {
  appDirectory: 'app',
  // SSR must stay on: the public /open/* and /image/* endpoints have to answer plain
  // GET/POST with JSON for the external blog-page, which SPA mode (HTML shell + data
  // endpoints) cannot provide.
  ssr: true,
} satisfies Config;
