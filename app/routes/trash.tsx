import React, { Suspense } from 'react';

const LazyTrashBinPage = React.lazy(() => import('../components/TrashBinPage'));

export default function TrashRoute() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyTrashBinPage />
    </Suspense>
  );
}
