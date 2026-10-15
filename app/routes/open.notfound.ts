// JSON 404 for the public API surface.
//
// FastAPI answered every unmatched path under its routers with {"detail":"Not Found"};
// React Router would otherwise render its HTML 404 page, which the external blog-page
// cannot parse. Registered as the `open/*` and `image/*` splats, so it only catches
// paths no concrete API route matched (concrete routes always win over splats).
import type { LoaderFunctionArgs } from 'react-router';

export function loader(_args: LoaderFunctionArgs): Response {
  return Response.json({ detail: 'Not Found' }, { status: 404 });
}

export { loader as action };
