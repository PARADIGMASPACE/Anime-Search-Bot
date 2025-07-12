CREATE TABLE IF NOT EXISTS favorites (
    anime_id BIGINT NOT NULL,
    user_id BIGINT,
    anime_title TEXT,
    original_title TEXT,
    last_episode INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, anime_id)
);