import { apiLoader, toLoginContext } from '~/server/http/handler';
import { imageLimiter, isAdmin } from '~/server/service/security';
import { getStatus } from '~/server/service/post';
import { getImageUrl } from '~/server/service/common';
import { forbidden } from '~/server/lib/httpError';
import { PostStatus } from '~/server/domain/enum';

// GET /image/post/:postId/:key — presigned image redirect with per-IP rate limit.
// Mirrors api/common.py image_api: non-admins may only fetch published posts' images.
// RedirectResponse(url) in Starlette defaults to a 307 redirect.
export const loader = apiLoader(async (ctx) => {
  await imageLimiter(ctx.realIp);

  const admin = await isAdmin(toLoginContext(ctx));
  if (!admin && getStatus(Number(ctx.params.postId)) !== PostStatus.PUBLISHED) {
    throw forbidden();
  }

  const url = await getImageUrl(`post/${ctx.params.postId}/${ctx.params.key}`);
  return new Response(null, { status: 307, headers: { location: url } });
});
