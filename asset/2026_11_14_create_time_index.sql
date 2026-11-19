-- The list queries filter deleted and sort on create_time DESC. A single-column create_time index
-- is ignored by the planner (it keeps ix_wwr_blog_post_deleted plus a temp B-tree sort); this
-- composite serves the filter and the ordering in one walk: 19.6ms -> 0.05ms on 50k rows, no ANALYZE.
CREATE INDEX IF NOT EXISTS ix_wwr_blog_post_deleted_create_time ON wwr_blog_post (deleted, create_time);

SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'wwr_blog_post';