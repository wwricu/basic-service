#!/usr/bin/env node
// Write-path smoke test for the RR7 port's admin API.
//
// Parity coverage for the mutating endpoints is deliberately limited to validation failures
// (test/parity.mjs must never write to the DB the legacy server shares). This script exercises
// the write cycles the admin SPA performs — tag create/update/soft delete/restore/hard delete and
// post create/update/publish/revert/soft delete/restore/hard delete — against the port, and then
// asserts the observable state (listings and counts) is back exactly as it was found.
//
// Run against the dev server (admin bypass under __debug__): node test/write-smoke.mjs

import { DatabaseSync } from 'node:sqlite';
import { resolve } from 'node:path';

const RR = process.env.RR_BASE ?? 'http://localhost:5199';
const DB = resolve(import.meta.dirname, '..', 'wwr.sqlite3');
const PROBE = 'zz-write-smoke';

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}${detail ? '  ' + detail : ''}`);
  if (!ok) failures++;
};

const db = new DatabaseSync(DB);
const tableState = (table, order = 'id') =>
  JSON.stringify(db.prepare(`SELECT * FROM ${table} ORDER BY ${order}`).all());
const snapshot = () =>
  JSON.stringify({
    post: tableState('wwr_blog_post'),
    tag: tableState('wwr_post_tag'),
    relation: tableState('wwr_entity_relation'),
    resource: tableState('wwr_post_resource'),
    config: tableState('wwr_sys_config', 'key'),
  });
const before = snapshot();

// Never leave probe rows in the shared dev DB, even when a step throws halfway through.
const probe = { tagId: null, postId: null };
process.on('exit', () => {
  try {
    if (probe.tagId) db.prepare('DELETE FROM wwr_post_tag WHERE id = ?').run(probe.tagId);
    if (probe.postId) {
      db.prepare('DELETE FROM wwr_entity_relation WHERE src_id = ?').run(probe.postId);
      db.prepare('DELETE FROM wwr_blog_post WHERE id = ?').run(probe.postId);
      db.prepare('DELETE FROM wwr_blog_post_search WHERE id = ?').run(probe.postId);
    }
  } catch {
    /* the database handle was already closed — nothing left to clean */
  }
});

async function api(path, init) {
  const res = await fetch(RR + path, init);
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: res.status, body };
}
const jsonInit = (method, payload) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});
const findTag = (name) =>
  db.prepare('SELECT id, deleted FROM wwr_post_tag WHERE name = ?').all(name);

// Start clean if a previous interrupted run left a probe tag behind.
for (const row of findTag(PROBE)) db.prepare('DELETE FROM wwr_post_tag WHERE id = ?').run(row.id);

// ---------------------------------------------------------------- tag cycle
console.log('--- tag cycle');
const created = await api('/api/tag/create', jsonInit('POST', { name: PROBE, type: 'post_tag' }));
check('POST /api/tag/create', created.status === 200 && created.body?.id > 0, JSON.stringify(created.body).slice(0, 140));
const tagId = created.body?.id;
probe.tagId = tagId;
check('tag row persisted', findTag(PROBE).length === 1);

const updated = await api('/api/tag/update', jsonInit('POST', { id: tagId, name: `${PROBE}-2`, type: 'post_tag' }));
check('POST /api/tag/update', updated.status === 200 && updated.body?.name === `${PROBE}-2`, JSON.stringify(updated.body).slice(0, 140));
check('renamed row persisted', findTag(PROBE).length === 0 && findTag(`${PROBE}-2`).length === 1);

const dup = await api('/api/tag/create', jsonInit('POST', { name: `${PROBE}-2`, type: 'post_tag' }));
check('duplicate create -> 409', dup.status === 409, JSON.stringify(dup.body).slice(0, 140));

const soft = await api(`/api/tag/delete/${tagId}`);
check('GET /api/tag/delete/:id', soft.status === 200, JSON.stringify(soft.body).slice(0, 80));
check('tag row soft-deleted', findTag(`${PROBE}-2`)[0]?.deleted === 1);

const tagTrash = await api('/api/manage/trash/all');
check(
  'trash list contains the tag',
  tagTrash.status === 200 && Array.isArray(tagTrash.body) && tagTrash.body.some((r) => r.id === tagId),
  `status ${tagTrash.status}`,
);

const restored = await api('/api/manage/trash/edit', jsonInit('POST', { id: tagId, type: 'Tag', delete: false }));
check('tag restored', restored.status === 200 && findTag(`${PROBE}-2`)[0]?.deleted === 0);

await api(`/api/tag/delete/${tagId}`);
const purged = await api('/api/manage/trash/edit', jsonInit('POST', { id: tagId, type: 'Tag', delete: true }));
check('tag hard deleted', purged.status === 200 && findTag(`${PROBE}-2`).length === 0);

// ---------------------------------------------------------------- post cycle
console.log('--- post cycle');
const newPost = await api('/api/post/create');
check('GET /api/post/create', newPost.status === 200 && newPost.body?.id > 0 && newPost.body?.status === 'draft', JSON.stringify(newPost.body).slice(0, 160));
const postId = newPost.body?.id;
probe.postId = postId;
check('draft row persisted', db.prepare('SELECT id FROM wwr_blog_post WHERE id = ?').get(postId) !== undefined);

const saved = await api(
  '/api/post/update',
  jsonInit('POST', {
    id: postId,
    title: 'zz-write-smoke-post',
    preview: 'zz smoke preview',
    content: '<p>zz smoke body</p>',
    status: 'draft',
    tag_id_list: [],
    category_id: null,
  }),
);
check('POST /api/post/update', saved.status === 200 && saved.body?.title === 'zz-write-smoke-post', JSON.stringify(saved.body).slice(0, 160));

const detail = await api(`/api/post/detail/${postId}`);
check('GET /api/post/detail/:id', detail.status === 200 && detail.body?.content === '<p>zz smoke body</p>');

const published = await api(`/api/post/status/${postId}?status=published`);
check('GET /api/post/status/:id?status=published', published.status === 200, JSON.stringify(published.body).slice(0, 120));
const inList = await api('/api/post/all', jsonInit('POST', { page_index: 1, page_size: 100 }));
check(
  'published post shows in post/all',
  inList.status === 200 && (inList.body?.data ?? []).some((p) => p.id === postId),
);

const searchable = await api('/open/post/search?keyword=zz');
check(
  'full-text search finds it',
  searchable.status === 200 && (searchable.body ?? []).some((p) => p.id === postId),
  JSON.stringify(searchable.body).slice(0, 120),
);

const backToDraft = await api(`/api/post/status/${postId}?status=draft`);
check('reverted to draft', backToDraft.status === 200);

const notDeletableWhilePublished = await api(`/api/post/delete/${postId}`);
check('GET /api/post/delete/:id on a draft', notDeletableWhilePublished.status === 200, JSON.stringify(notDeletableWhilePublished.body).slice(0, 120));
check('post row soft-deleted', db.prepare('SELECT deleted FROM wwr_blog_post WHERE id = ?').get(postId)?.deleted === 1);

const postTrash = await api('/api/manage/trash/all');
check(
  'trash list contains the post',
  Array.isArray(postTrash.body) && postTrash.body.some((r) => r.id === postId && r.type === 'Post'),
);

// Pre-existing quirk of the legacy backend, reproduced on purpose: post_service.process_trash
// restores through post_db.update_selective, whose WHERE clause already requires
// deleted == False, so a deleted post can never be restored (tags go through
// common_db.recover and are fine). The port keeps the behaviour instead of fixing it.
const postRestored = await api('/api/manage/trash/edit', jsonInit('POST', { id: postId, type: 'Post', delete: false }));
check('post restore is the legacy no-op', postRestored.status === 200 && db.prepare('SELECT deleted FROM wwr_blog_post WHERE id = ?').get(postId)?.deleted === 1);

await api(`/api/post/delete/${postId}`);
const postPurged = await api('/api/manage/trash/edit', jsonInit('POST', { id: postId, type: 'Post', delete: true }));
check('post hard deleted', postPurged.status === 200 && db.prepare('SELECT id FROM wwr_blog_post WHERE id = ?').get(postId) === undefined);

// Both backends leave the FTS5 row behind after a hard delete (it is only visible through the
// post join), so the probe removes its own residue here rather than pretending the app did.
db.prepare('DELETE FROM wwr_blog_post_search WHERE id = ?').run(postId);

// ---------------------------------------------------------------- end state
const listing = await api('/api/tag/all', jsonInit('POST', { page_index: 0, page_size: 0, type: 'post_tag' }));
check('tag/all back to original', Array.isArray(listing.body) && !listing.body.some((t) => t.id === tagId));
const postList = await api('/api/post/all', jsonInit('POST', { page_index: 1, page_size: 100 }));
check('post/all back to original', postList.status === 200 && !(postList.body?.data ?? []).some((p) => p.id === postId));
check('database back to original', snapshot() === before);

db.close();
console.log(`\n${failures === 0 ? 'WRITE SMOKE TEST PASSED' : failures + ' WRITE SMOKE FAILURES'}`);
process.exit(failures === 0 ? 0 : 1);
