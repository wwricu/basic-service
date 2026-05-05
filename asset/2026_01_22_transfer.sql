ALTER TABLE wwr_blog_post       RENAME TO wwr_blog_post_old;
ALTER TABLE wwr_post_tag        RENAME TO wwr_post_tag_old;
ALTER TABLE wwr_entity_relation RENAME TO wwr_entity_relation_old;
ALTER TABLE wwr_post_resource   RENAME TO wwr_post_resource_old;
ALTER TABLE wwr_sys_config      RENAME TO wwr_sys_config_old;

CREATE TABLE wwr_blog_post (
    title VARCHAR NOT NULL,
    cover_id INTEGER,
    content TEXT NOT NULL,
    preview TEXT NOT NULL,
    status VARCHAR NOT NULL,
    category_id INTEGER,
    id INTEGER NOT NULL,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_post_tag (
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    count INTEGER NOT NULL,
    id INTEGER NOT NULL,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_entity_relation (
    src_id INTEGER NOT NULL,
    dst_id INTEGER NOT NULL,
    type VARCHAR NOT NULL,
    id INTEGER NOT NULL,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_post_resource (
    post_id INTEGER NOT NULL,
    name VARCHAR,
    "key" VARCHAR NOT NULL,
    type VARCHAR,
    url TEXT,
    id INTEGER NOT NULL,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE wwr_sys_config (
    "key" VARCHAR NOT NULL,
    value TEXT,
    id INTEGER NOT NULL,
    deleted BOOLEAN NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    UNIQUE ("key")
);

INSERT INTO wwr_blog_post       SELECT * FROM wwr_blog_post_old;
INSERT INTO wwr_post_tag        SELECT * FROM wwr_post_tag_old;
INSERT INTO wwr_entity_relation SELECT * FROM wwr_entity_relation_old;
INSERT INTO wwr_post_resource   SELECT * FROM wwr_post_resource_old;
INSERT INTO wwr_sys_config      SELECT * FROM wwr_sys_config_old;

DROP TABLE wwr_blog_post_old;
DROP TABLE wwr_post_tag_old;
DROP TABLE wwr_entity_relation_old;
DROP TABLE wwr_post_resource_old;
DROP TABLE wwr_sys_config_old;

CREATE INDEX ix_wwr_blog_post_title ON wwr_blog_post (title);
CREATE INDEX ix_wwr_blog_post_category_id ON wwr_blog_post (category_id);
CREATE INDEX ix_wwr_blog_post_deleted ON wwr_blog_post (deleted);
CREATE INDEX ix_wwr_blog_post_status ON wwr_blog_post (status);
CREATE INDEX ix_wwr_post_tag_name ON wwr_post_tag (name);
CREATE INDEX ix_wwr_post_tag_type ON wwr_post_tag (type);
CREATE INDEX ix_wwr_post_tag_deleted ON wwr_post_tag (deleted);
CREATE INDEX ix_wwr_entity_relation_src_id ON wwr_entity_relation (src_id);
CREATE INDEX ix_wwr_entity_relation_dst_id ON wwr_entity_relation (dst_id);
CREATE INDEX ix_wwr_entity_relation_type ON wwr_entity_relation (type);
CREATE INDEX ix_wwr_entity_relation_deleted ON wwr_entity_relation (deleted);
CREATE INDEX ix_wwr_post_resource_deleted ON wwr_post_resource (deleted);
CREATE INDEX ix_wwr_post_resource_type ON wwr_post_resource (type);
CREATE INDEX ix_wwr_post_resource_post_id ON wwr_post_resource (post_id);
CREATE INDEX ix_wwr_sys_config_deleted ON wwr_sys_config (deleted);
