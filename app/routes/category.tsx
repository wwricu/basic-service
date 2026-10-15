import React, { Suspense } from 'react';
import { TagType } from '~/server/domain/enum';

const LazyTagTable = React.lazy(() => import('~/components/TagTable'));

export default function CategoryRoute() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyTagTable tagType={TagType.POST_CAT} />
    </Suspense>
  );
}
