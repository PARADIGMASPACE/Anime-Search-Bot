CREATE TABLE IF NOT EXISTS languages (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

INSERT INTO languages (code, name) VALUES
('en', 'English'),
('ru', 'Русский')
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    user_language TEXT DEFAULT 'EN',
    preferred_language_id INTEGER REFERENCES languages(id) ON DELETE SET NULL,
    CONSTRAINT unique_telegram_user_id UNIQUE (telegram_user_id)
);


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
