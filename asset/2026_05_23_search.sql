ALTER TABLE wwr_blog_post ADD COLUMN raw_content TEXT NOT NULL DEFAULT '';
CREATE VIRTUAL TABLE wwr_blog_post_search USING fts5(
    content_rowid='id',
    title,
    preview,
    raw_content,
    content='wwr_blog_post',
    tokenize='trigram'
);
