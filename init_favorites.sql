CREATE TABLE IF NOT EXISTS anime (
    id SERIAL PRIMARY KEY,
    title_original TEXT,
    title_ru TEXT,
    id_anilist BIGINT,
    id_shikimori BIGINT,
    total_episodes_relase INTEGER DEFAULT 0,
    UNIQUE(id_anilist),
    UNIQUE(id_shikimori)
);


CREATE TABLE IF NOT EXISTS favorites (
    user_id BIGINT NOT NULL,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, anime_id)
);
