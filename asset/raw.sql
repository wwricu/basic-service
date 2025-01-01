CREATE TABLE wwr_blog_post
(
    title       VARCHAR(64)                          NOT NULL,
    cover_id    INTEGER,
    content     TEXT                                 NOT NULL,
    preview     TEXT                                 NOT NULL,
    status      VARCHAR(32)                          NOT NULL,
    category_id INTEGER,
    id          INTEGER                              NOT NULL,
    deleted     BOOLEAN                              NOT NULL,
    create_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    update_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_post_tag
(
    name        VARCHAR(64)                          NOT NULL,
    type        VARCHAR(32)                          NOT NULL,
    id          INTEGER                              NOT NULL,
    deleted     BOOLEAN                              NOT NULL,
    create_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    update_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_post_tag_relation
(
    post_id     INTEGER                              NOT NULL,
    tag_id      INTEGER                              NOT NULL,
    id          INTEGER                              NOT NULL,
    deleted     BOOLEAN                              NOT NULL,
    create_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    update_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_entity_tag_relation
(
    src_id      INTEGER                              NOT NULL,
    dst_id      INTEGER                              NOT NULL,
    type        VARCHAR(32)                          NOT NULL,
    id          INTEGER                              NOT NULL,
    deleted     BOOLEAN                              NOT NULL,
    create_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    update_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_post_resource
(
    post_id     INTEGER                              NOT NULL,
    name        VARCHAR(64),
    "key"       VARCHAR(128)                         NOT NULL,
    type        VARCHAR(32),
    url         TEXT,
    id          INTEGER                              NOT NULL,
    deleted     BOOLEAN                              NOT NULL,
    create_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    update_time DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX ix_wwr_blog_post_status ON wwr_blog_post (status);
CREATE INDEX ix_wwr_blog_post_deleted ON wwr_blog_post (deleted);
CREATE INDEX ix_wwr_blog_post_title ON wwr_blog_post (title);
CREATE INDEX ix_wwr_post_tag_deleted ON wwr_post_tag (deleted);
CREATE INDEX ix_wwr_post_tag_relation_deleted ON wwr_post_tag_relation (deleted);
CREATE INDEX ix_wwr_entity_tag_relation_dst_id ON wwr_entity_tag_relation (dst_id);
CREATE INDEX ix_wwr_entity_tag_relation_deleted ON wwr_entity_tag_relation (deleted);
CREATE INDEX ix_wwr_entity_tag_relation_src_id ON wwr_entity_tag_relation (src_id);
CREATE INDEX ix_wwr_post_resource_post_id ON wwr_post_resource (post_id);
CREATE INDEX ix_wwr_post_resource_deleted ON wwr_post_resource (deleted);
