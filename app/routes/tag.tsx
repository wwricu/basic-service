import React, { Suspense } from 'react';
import { TagType } from '~/server/domain/enum';

const LazyTagTable = React.lazy(() => import('~/components/TagTable'));

export default function TagRoute() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyTagTable tagType={TagType.POST_TAG} />
    </Suspense>
  );
}
