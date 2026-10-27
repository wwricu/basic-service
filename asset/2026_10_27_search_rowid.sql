-- The search index stops carrying an id column: BlogPost.id now joins on the FTS5 rowid,
-- so the id is no longer tokenised into the index and bm25() weights line up with title/preview/search_content.
-- Run this with basic-service stopped.

-- Pre-check: must return 0, otherwise a rowid collision would silently drop rows below.
SELECT COUNT(*) AS non_numeric_id FROM wwr_blog_post_search WHERE id NOT GLOB '[0-9]*';

CREATE VIRTUAL TABLE wwr_blog_post_search_new USING fts5(
    title,
    preview,
    search_content
);

INSERT INTO wwr_blog_post_search_new(rowid, title, preview, search_content)
SELECT CAST(id AS INTEGER), title, preview, search_content FROM wwr_blog_post_search;

DROP TABLE wwr_blog_post_search;
ALTER TABLE wwr_blog_post_search_new RENAME TO wwr_blog_post_search;

-- Post-check: the two counts must match the row count of the table before the migration.
SELECT (SELECT COUNT(*) FROM wwr_blog_post_search) AS indexed,
       (SELECT COUNT(*) FROM wwr_blog_post WHERE deleted = 0) AS live_posts;
