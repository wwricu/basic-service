import type { ActionFunctionArgs, LoaderFunctionArgs } from 'react-router';
import { dispatch } from '~/server/http/router';

// Single colocated route mirroring the legacy /api/* surface.
//
// The admin pages keep their existing http.get/post('/api/...') calls; this route
// receives them, strips the /api prefix, and dispatches in-process to the shared
// service layer (no second backend, no cross-service HTTP).
//
// Both loader and action are exported because the legacy surface has GET endpoints
// (e.g. /post/detail/:id, /manage/config/get) as well as POST ones — React Router
// only routes non-GET requests to `action`.
async function handle({ request }: ActionFunctionArgs | LoaderFunctionArgs): Promise<Response> {
  const url = new URL(request.url);
  let raw = url.pathname.replace(/^\/api\//, '');
  if (raw.endsWith('/')) {
    raw = raw.slice(0, -1);
  }
  return dispatch(request, raw);
}

export async function loader(args: LoaderFunctionArgs) {
  return handle(args);
}

export async function action(args: ActionFunctionArgs) {
  return handle(args);
}

// No `default`/`ErrorBoundary` export on purpose: React Router only short-circuits into
// its raw-response "resource route" path when the matched leaf module renders nothing.
// A component export here would make every /api call return the HTML app shell instead
// of the dispatcher's JSON.
