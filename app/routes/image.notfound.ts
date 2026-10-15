// JSON 404 for unmatched /image/* paths — see app/routes/open.notfound.ts for the rationale.
import type { LoaderFunctionArgs } from 'react-router';

export function loader(_args: LoaderFunctionArgs): Response {
  return Response.json({ detail: 'Not Found' }, { status: 404 });
}

export { loader as action };
