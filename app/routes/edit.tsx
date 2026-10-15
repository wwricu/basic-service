import React, { Suspense } from 'react';
import ClientOnly, { PageLoading } from '~/components/ClientOnly';

const LazyEditor = React.lazy(() => import('~/components/EditorPage'));

export default function EditRoute() {
  // EditorPage mounts CKEditor and the antd-img-crop cover uploader, both of which need real
  // DOM; the legacy SPA created them in the browser only, so the SSR pass stops at the fallback.
  return (
    <ClientOnly fallback={<PageLoading />}>
      <Suspense fallback={<PageLoading />}>
        <LazyEditor />
      </Suspense>
    </ClientOnly>
  );
}
