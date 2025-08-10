# Anime Search Bot

A Telegram bot for searching anime information, adding titles to favorites, and receiving notifications about new episode releases. Built with asynchronous Python, it integrates APIs from AniList and Shikimori, uses Redis for efficient caching to minimize API calls, and PostgreSQL for persistent storage. Translations of descriptions are handled via LibreTranslate. The bot emphasizes speed, scalability, and clean architecture.

- **Anime Search**: Search for any anime by name and get detailed info including:
  - Title (original and Russian)
  - Type (e.g., TV-series)
  - Status (e.g., Announced)
  - Genres (e.g., Action, Adventure, Fantasy)
  - Episode count
  - Description (translated if needed)
  - Photo/poster

- **Favorites Management**: Add anime to favorites, view list, delete entries, and get quick info on favorited titles.

- **Episode Notifications**: Automatic checks twice a day (via APScheduler) against AniList API for all anime in the database. If the episode count increases, users who favorited it receive Telegram notifications.

- **Multi-Language Support**: Choose English or Russian (/language command). Descriptions from AniList are translated using LibreTranslate.

- **Commands**:
  - `/start`: Initialize bot, choose language.
  - Text input: Search anime by name.
  - `/favorites`: View favorites list with options to delete or view info.
  - `/language`: Change language.

- **Performance Optimizations**: Multi-level Redis caching (anime info, favorites, searches, users) to reduce API requests and boost response speed. Asynchronous handling with aiogram and aiohttp.

## Tech Stack

- **Framework**: Aiogram (Telegram Bot API, async)
- **APIs**: AniList, Shikimori (parallel queries for comprehensive data), LibreTranslate (for descriptions)
- **Database**: PostgreSQL (users, anime, favorites, languages)
- **Caching**: Redis (stateful, multi-layered for anime, favorites, searches, users)
- **Scheduler**: APScheduler (episode checks)
- **Other Libraries**:
  - aiohttp==3.12.13
  - aiogram==3.21.0
  - redis==5.2.0
  - python-dotenv==1.1.1
  - asyncpg==0.29.0
  - APScheduler==3.11.0
  - loguru
  - requests==2.32.4
  - httpx
  - bleach
  - Testing: pytest, pytest-asyncio, pytest-cov
  - Linting: ruff, black, isort
  - Security: bandit, safety

- **Deployment**: Docker Compose (includes PostgreSQL, Redis, LibreTranslate)
- **Architecture Highlights**:
  - Asynchronous design for high concurrency.
  - Modular structure: API integrations, services (anime/favorites), handlers (search, favorites, nav), middleware (antiflood, language).
  - DB Schema:
    ```sql
    CREATE TABLE IF NOT EXISTS languages (
        id SERIAL PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL
    );
    -- Default inserts: ('en', 'English'), ('ru', 'Русский')

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_user_id BIGINT NOT NULL UNIQUE,
        user_language TEXT DEFAULT 'EN'
    );

    CREATE TABLE IF NOT EXISTS anime (
        id SERIAL PRIMARY KEY,
        title_original TEXT,
        title_ru TEXT,
        id_anilist BIGINT UNIQUE,
        id_shikimori BIGINT UNIQUE,
        total_episodes_relase INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS favorites (
        user_id BIGINT NOT NULL,
        anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, anime_id)
    );
    ```
  - Caching reduces API load: Stores anime details, user data, etc., making the bot responsive even under load.

## Installation

1. Clone the repository:
   ```
   git clone <repo-url>
   cd <repo-dir>
   ```

2. Create `.env` file:
   ```
   TOKEN=telegram-bot-token
   ```
   - Obtain `telegram-bot-token` from BotFather on Telegram.

3. Build and run with Docker Compose:
   ```
   docker-compose up --build -d
   ```
   - This sets up the bot, PostgreSQL, Redis, and LibreTranslate.
   - Initialize favorites DB if needed: Run `init_favorites.sql` manually or via bot startup.

## Usage

1. Start the bot in Telegram: `/start`
2. Choose language (English/Russian).
3. Search anime: Send the name as text (e.g., "Naruto").
4. Add to favorites from search results.
5. View/manage favorites: `/favorites`
6. Change language: `/language`
7. Notifications: Automatically sent for new episodes on favorited anime (checks run twice daily).

## Testing

- Run tests locally:
  ```
  pytest -v
  ```
- Focus: Database operations (users, anime, favorites), services (anime/favorite logic), utils (caption formatting).
- Coverage: Generated via `--cov` flag (e.g., `pytest --cov=database --cov=services --cov=utils`).

## CI/CD

GitHub Actions workflow (`ci.yml`):
- Triggers: Push/PR to `main` or `develop`.
- Jobs:
  - **Test**: Sets up Python 3.11, Postgres/Redis services, installs deps, creates test DB tables, runs `pytest -v`, generates coverage.
  - **Lint**: Runs ruff, black (--check), isort (--check-only) for code quality.

No CD deployment; manual `docker-compose` for production.

## Contributing

Pull requests welcome! Follow these steps:
1. Fork the repo.
2. Create a branch: `git checkout -b feature/xyz`.
3. Commit changes.
4. Push and open PR.

Ensure tests pass and linting is clean.

## License

MIT License.
