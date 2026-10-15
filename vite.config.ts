import { reactRouter } from '@react-router/dev/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [reactRouter(), tsconfigPaths()],
  ssr: {
    // antd and @ant-design/icons ship ESM with extensionless internal specifiers
    // (e.g. `es/icons/BarsOutlined`), which Node's ESM resolver rejects during SSR.
    // Bundling them into the server build lets Vite resolve those paths.
    // Their transitive deps need the same treatment: @ant-design/cssinjs imports
    // `@babel/runtime/helpers/esm/*` (ESM files inside a CJS package) and
    // `@emotion/hash` (CJS whose interop default is not callable), both of which
    // break when Vite leaves them external for the Node SSR runtime.
    noExternal: [
      'antd',
      '@ant-design/icons',
      'antd-img-crop',
      'ckeditor5',
      '@ckeditor/ckeditor5-react',
      /^rc-/,
      /^@rc-component\//,
      /^@ant-design\//,
      /^@emotion\//,
      /^@babel\/runtime/,
      /^@ctrl\//,
    ],
    // The native node binding is server-only: loader/action exports are stripped from the
    // browser bundle by the React Router vite plugin, so the client dependency scanner must
    // not try to prebundle it (its `browser` field points at a wasm package we don't install).
    external: ['@node-rs/jieba'],
  },
  optimizeDeps: {
    exclude: ['@node-rs/jieba'],
  },
});
