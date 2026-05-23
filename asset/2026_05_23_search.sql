ALTER TABLE wwr_blog_post ADD COLUMN search_content TEXT NOT NULL DEFAULT '';
CREATE VIRTUAL TABLE blog_post_search USING fts5(
    content_rowid='id',
    title,
    preview,
    search_content,
    content='wwr_blog_post'
);
