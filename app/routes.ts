import { type RouteConfig, route, index, layout } from '@react-router/dev/routes';

// React Router v7 route manifest.
//
//  - Public JSON API (exact legacy paths, consumed by the external blog-page):
//      /open/*, /image/post/:postId/:key
//  - /api/* is an in-process dispatcher: the admin pages call the legacy
//      /api/<path> URLs and land directly on the shared server-side service layer,
//      so there is no second backend and no cross-service HTTP hop.
//  - Admin UI pages render inside the pathless AdminLayout (antd theme + sider/menu).
export default [
  // ---- Public open API (unchanged wire contract for blog-page) ----
  route('open/post/all', 'routes/open.posts.ts'),
  route('open/post/search', 'routes/open.search.ts'),
  route('open/post/detail/:postId', 'routes/open.detail.ts'),
  route('open/tags/:tagType', 'routes/open.tags.ts'),
  route('open/about', 'routes/open.about.ts'),
  // Unmatched /open and /image paths stay JSON (FastAPI's {"detail":"Not Found"}) instead
  // of React Router's HTML 404 page; concrete routes above still win over these splats.
  route('open/*', 'routes/open.notfound.ts'),
  route('image/post/:postId/:key', 'routes/image.ts'),
  route('image/*', 'routes/image.notfound.ts'),

  // ---- In-process admin API dispatcher ----
  route('api/*', 'routes/api.$.tsx'),

  // ---- Auth ----
  route('login', 'routes/login.tsx'),

  // ---- Admin UI (pathless layout, mirrors the legacy SPA routes) ----
  layout('components/AdminLayout.tsx', [
    index('routes/index.tsx'),
    route('post', 'routes/post.tsx'),
    route('draft', 'routes/draft.tsx'),
    route('category', 'routes/category.tsx'),
    route('tag', 'routes/tag.tsx'),
    route('management', 'routes/management.tsx'),
    route('task', 'routes/task.tsx'),
    route('trash', 'routes/trash.tsx'),
    route('edit/:id', 'routes/edit.tsx'),
  ]),
] satisfies RouteConfig;
