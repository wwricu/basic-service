import * as commonDb from '~/server/db/common';
import * as tagDb from '~/server/db/tag';
import { conflict, badRequest, notFound, HttpError } from '~/server/lib/httpError';
import { POST_TAG_TABLE } from '~/server/db/tag';
import type { PostTagRow, TagRO, TagVO, TagQueryDTO, TrashBinRO } from '~/server/domain/types';

// Mirrors wwricu/service/tag.py. DB rows are PostTag shapes; VO keeps the wire field names.
//
// TagRO.type is `TagTypeEnum | None = POST_TAG`: an omitted field arrives as post_tag from the
// model default, an explicit null stays null and reaches TagQueryDTO(type=None), which drops the
// type filter from the duplicate check. Both paths are reproduced here, message text included
// (Python f-strings render None as "None").

/** Python's `f'{value}'` for the enum-or-None fields the legacy messages interpolate. */
const pyText = (value: string | null | undefined): string =>
  value === null || value === undefined ? 'None' : value;

function toVO(row: PostTagRow): TagVO {
  return { id: row.id, name: row.name, type: row.type as TagVO['type'], count: row.count ?? null };
}

export async function create(tagCreate: TagRO): Promise<TagVO> {
  const type = tagCreate.type ?? null;
  const dupQuery: TagQueryDTO = { name: tagCreate.name, type };
  if (tagDb.count(dupQuery) > 0) {
    throw conflict(`${pyText(type)} ${tagCreate.name} already exists`);
  }
  if (type === null) {
    // PostTag.type is NOT NULL; SQLAlchemy aborted the insert and FastAPI answered 500.
    throw new HttpError(500, 'Internal Server Error');
  }
  const row = commonDb.insert<PostTagRow>(POST_TAG_TABLE, 'id', { name: tagCreate.name, type });
  return toVO(row);
}

export async function update(tagUpdate: TagRO): Promise<TagVO> {
  if (tagUpdate.id === undefined || tagUpdate.id === null) throw badRequest();
  const tags = tagDb.findByCriteria({ tag_ids: [tagUpdate.id] });
  const tag = tags[0];
  if (!tag) {
    throw notFound(`${pyText(tagUpdate.type ?? null)} not found`);
  }
  if (tag.name === tagUpdate.name) return toVO(tag);
  const type = tagUpdate.type ?? null;
  if (tagDb.count({ name: tagUpdate.name, type }) > 0) {
    throw conflict(`${pyText(type)} ${tagUpdate.name} already exists`);
  }
  tag.name = tagUpdate.name;
  tagDb.updateSelective(tagUpdate.id, { name: tagUpdate.name });
  return toVO(tag);
}

export async function processTrash(trashBin: TrashBinRO): Promise<void> {
  if (trashBin.delete) {
    commonDb.hardDelete(POST_TAG_TABLE, trashBin.id);
  } else {
    commonDb.recover(POST_TAG_TABLE, trashBin.id);
  }
}
