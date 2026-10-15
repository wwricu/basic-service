import React, { Suspense } from 'react';

const LazyTaskPage = React.lazy(() => import('../components/TaskPage'));

export default function TaskRoute() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyTaskPage />
    </Suspense>
  );
}
