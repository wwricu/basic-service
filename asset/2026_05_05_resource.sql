ALTER TABLE wwr_post_resource RENAME TO wwr_post_resource_old;

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
    PRIMARY KEY (id),
    UNIQUE ("key")
);

INSERT INTO wwr_post_resource SELECT * FROM wwr_post_resource_old;
DROP TABLE wwr_post_resource_old;

CREATE INDEX ix_wwr_post_resource_post_id ON wwr_post_resource (post_id);
CREATE INDEX ix_wwr_post_resource_type ON wwr_post_resource (type);
CREATE INDEX ix_wwr_post_resource_deleted ON wwr_post_resource (deleted);
