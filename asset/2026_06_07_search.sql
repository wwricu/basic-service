ALTER TABLE wwr_blog_post RENAME TO wwr_blog_post_old;
CREATE TABLE wwr_blog_post (
    id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    cover_id INTEGER,
    content TEXT NOT NULL,
    preview TEXT NOT NULL,
    status VARCHAR NOT NULL,
    category_id INTEGER,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);
INSERT INTO  wwr_blog_post SELECT id, title, cover_id, content, preview, status, category_id, deleted, create_time, update_time FROM wwr_blog_post_old;
DROP TABLE   wwr_blog_post_old;
CREATE INDEX ix_wwr_blog_post_title       ON wwr_blog_post (title);
CREATE INDEX ix_wwr_blog_post_category_id ON wwr_blog_post (category_id);
CREATE INDEX ix_wwr_blog_post_deleted     ON wwr_blog_post (deleted);
CREATE INDEX ix_wwr_blog_post_status      ON wwr_blog_post (status);


DROP TABLE IF EXISTS wwr_blog_post_search;
CREATE VIRTUAL TABLE wwr_blog_post_search USING fts5(
    id,
    title,
    preview,
    search_content
);
