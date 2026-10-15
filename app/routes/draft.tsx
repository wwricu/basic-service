import React, { Suspense } from 'react';
import { PostStatus } from '~/server/domain/enum';

const LazyPostTable = React.lazy(() => import('~/components/PostTable'));

export default function DraftRoute() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyPostTable postStatus={PostStatus.DRAFT} />
    </Suspense>
  );
}
