# Repository Guidelines

## Project Overview

Python async service that scrapes Telegram channels for job posts, scores them against user resumes via LLM, and forwards matches to users via a Telegram bot. PostgreSQL for storage, APScheduler for scheduling.

## Key Architecture Facts

- **Two Telegram client libraries in use**: Telethon (`services/telegram_scraper.py`) scrapes channels; `python-telegram-bot` (`services/bot_handler.py`, `services/forwarding_service.py`) handles bot commands and message forwarding. Don't confuse their APIs.
- **Lazy-initialized singletons**: DB engine (`db/engine.py`), Telethon client (`services/telegram_scraper.py`), Bot instance (`services/forwarding_service.py`), and OpenAI client (`services/scoring_service.py`) all use `_var = None` + getter pattern. Nothing connects at import time — first call to `get_session()`, `_get_client()`, `_get_bot()`, or `_ensure_initialized()` triggers initialization.
- **DB auto-creates**: `build_engine()` creates the database if missing and runs `Base.metadata.create_all()` on every startup. No migration tool is configured.
- **Scoring uses OpenAI Agents SDK** (`agents` package), not raw OpenAI API. Structured output via Pydantic model `ScoringResult`. LLM is configured via `llm_api_key`/`llm_base_url` env vars (supports non-OpenAI endpoints). Scoring prompt is in `services/scoring_constants.py`.
- **`telethon_msg_to_model.py`** at repo root converts raw Telethon `Message` objects to Pydantic `TelegramMessage`. Used only by the scraper.
- **`main.py`** starts both a Telegram bot (polling) and APScheduler concurrently. All three jobs (fetch, evaluate, forward) run once on startup, then on intervals.

## Commands

```powershell
# Setup
python -m venv scraper_env
.\scraper_env\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the full service (bot + scheduler)
python main.py
```

No test suite, linter, or formatter is configured. No build step.

## Required Environment Variables

All loaded from `.env` via pydantic-settings (`config.py`):

| Variable | Purpose |
|---|---|
| `telegram_api_id`, `telegram_api_hash`, `telegram_phone` | Telethon user-session auth |
| `telegram_bot_token` | python-telegram-bot bot token |
| `database_url` | PostgreSQL connection string |
| `telegram_channels` | Comma-separated list of channel usernames to scrape |
| `llm_api_key`, `llm_base_url` | OpenAI-compatible LLM endpoint |
| `scoring_model` | Model name for the scoring agent |
| `fetch_interval_minutes`, `evaluate_interval_minutes`, `forward_interval_minutes` | Scheduler intervals |
| `scoring_batch_size`, `scoring_max_concurrent` | Scoring concurrency controls |
| `forward_score_threshold`, `forward_max_concurrent` | Forwarding thresholds |

## Coding Conventions

- 4-space indentation, standard Python style.
- `snake_case` for files/functions, `PascalCase` for classes/Pydantic models, `UPPER_SNAKE_CASE` for constants.
- Business logic in `jobs/`, external integrations in `services/`, persistence in `db/repos/`, table definitions in `db/models/`.
- Pydantic schemas in `schemas/` for cross-module data transfer.
- Typed function signatures preferred.

## Security

Never commit: `.env`, `session_name.session` (Telethon session), API keys, database URLs. These are in `.gitignore`.
