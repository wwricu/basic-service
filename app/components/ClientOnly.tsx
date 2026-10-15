import { useEffect, useState, type ReactNode } from 'react';

interface Props {
  // What the server (and the pre-hydration browser) shows — the SPA's own Suspense fallback.
  fallback: ReactNode;
  children: ReactNode;
}

/**
 * Render children only in the browser.
 *
 * The admin pages came from a client-only SPA: they fetch everything in an effect, so there is
 * no server-renderable content, and two of them additionally build real DOM while mounting —
 * CKEditor (domDocument.createElement) and antd-img-crop (canvas). Rendering those on the server
 * throws and React Router answers 500. Gating on mount keeps the server pass at the same
 * "Loading..." the SPA showed before its lazy chunk resolved, and the page then behaves exactly
 * as it did in the browser-only original.
 */
export default function ClientOnly({ fallback, children }: Props): ReactNode {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  return <>{mounted ? children : fallback}</>;
}

export const PageLoading = (): ReactNode => <div>Loading...</div>;
