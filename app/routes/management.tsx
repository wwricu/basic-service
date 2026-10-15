import React, { Suspense } from 'react';
import ClientOnly, { PageLoading } from '~/components/ClientOnly';

const LazyManagement = React.lazy(() => import('../components/ManagePage'));

export default function ManagementRoute() {
  // ManagePage pulls in the about-page CKEditor; the ckeditor5 bundle touches window/document
  // while its modules evaluate, so the page must not be imported during the SSR pass at all.
  return (
    <ClientOnly fallback={<PageLoading />}>
      <Suspense fallback={<PageLoading />}>
        <LazyManagement />
      </Suspense>
    </ClientOnly>
  );
}
