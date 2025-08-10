# Anime Search Bot

A Telegram bot for searching anime information, managing favorites, and receiving notifications about new episode releases.  
Built with asynchronous Python, it integrates AniList and Shikimori APIs, uses Redis caching to reduce API calls, and PostgreSQL for storage.  
Descriptions are translated via LibreTranslate.  
Focus on speed, scalability, and clean architecture.

## Features

### Anime Search
Search anime by name with details including:
- Original and Russian titles
- Type (e.g., TV-series)
- Status (e.g., Announced)
- Genres (Action, Adventure, Fantasy)
- Episode count
- Translated description
- Poster image

### Favorites Management
Add, view, delete favorites; quick info on favorited anime.

### Episode Notifications
Twice-daily automated checks (APScheduler) to AniList API.  
Users get Telegram notifications on new episodes.

### Multi-language Support
English and Russian selectable via `/language` command.  
Descriptions auto-translated with LibreTranslate.

## Performance Optimizations
- Multi-layer Redis caching for anime, favorites, searches, users to reduce API requests.
- Asynchronous handling with aiogram and aiohttp.

## Tech Stack
- **Python** 3.10+
- **Aiogram** (Telegram Bot API, async)
- **AniList and Shikimori APIs** (parallel queries)
- **LibreTranslate API** for description translation
- **PostgreSQL** for users, anime, favorites, languages
- **Redis** for caching
- **APScheduler** for episode checks
- **Docker Compose** to run bot, DB, Redis, LibreTranslate

## Installation
1. Clone repository:  
   ```
   git clone https://github.com/PARADIGMASPACE/Anime-Search-Bot.git
   cd Anime-Search-Bot
   ```

2. Create `.env` file with variables:  
   ```
   TOKEN=your_telegram_bot_token
   ```

3. Run with Docker Compose:  
   ```
   docker-compose up -d --build
   ```

## Usage
- Start bot in Telegram: `/start`
- Select language (English or Russian)
- Search anime by sending its name
- Manage favorites with `/favorites`
- Change language with `/language`
- Receive notifications on new episodes for favorites

## Project Structure
- `bot.py` - Entry point
- `handlers/` - Telegram handlers (commands, callbacks)
- `services/` - API integrations, business logic
- `database/` - DB interactions
- `middleware/` - Logging, antiflood, language
- `utils/` - Helpers and utilities
- `tests/` - Automated tests

## Database Schema (PostgreSQL)
```sql
TABLE languages
  id SERIAL PRIMARY KEY
  code TEXT UNIQUE NOT NULL
  name TEXT NOT NULL
  -- Defaults: ('en', 'English'), ('ru', 'Русский')

TABLE users
  id SERIAL PRIMARY KEY
  telegram_user_id BIGINT UNIQUE NOT NULL
  user_language TEXT DEFAULT 'EN'

TABLE anime
  id SERIAL PRIMARY KEY
  title_original TEXT
  title_ru TEXT
  id_anilist BIGINT UNIQUE
  id_shikimori BIGINT UNIQUE
  total_episodes_relase INTEGER DEFAULT 0

TABLE favorites
  user_id BIGINT NOT NULL REFERENCES users(telegram_user_id) ON DELETE CASCADE
  anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE
  PRIMARY KEY (user_id, anime_id)
```

## Testing
Run tests:  
```
pytest -v tests/
```

Generate coverage:  
```
pytest --cov=database --cov=services --cov=utils
```

## CI/CD
GitHub Actions:
- Runs on push/PR to main or develop branches
- Tests with Python 3.11, Postgres, Redis services
- Linting with ruff, black (check), isort
- Deployment manual via Docker Compose

## Commands
| Command    | Description                  |
|------------|------------------------------|
| `/start`   | Start bot, select language   |
| `/favorites` | View and manage favorites  |
| `/language` | Change bot language         |
| Text input | Search anime by name         |

## Contributing
Fork repo → create branch → commit → PR.  
Ensure tests pass and linting clean.

## License
MIT License