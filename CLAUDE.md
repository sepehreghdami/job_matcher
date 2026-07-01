# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python async service that scrapes Telegram channels for job posts, scores them against user resumes via an LLM, and forwards high-scoring matches to users through a Telegram bot. PostgreSQL for storage, APScheduler for scheduling.

## Commands

```bash
# Install/update dependencies (creates/updates .venv from pyproject.toml + uv.lock)
uv sync

# Run the full service (scheduler + jobs; bot polling optional, see main.py)
uv run python main.py
```

Dependencies are managed with [uv](https://docs.astral.sh/uv/) via `pyproject.toml`/`uv.lock` — do not add to or reintroduce `requirements.txt`. Add a new dependency with `uv add <package>`.

There is no test suite, linter, formatter, or build step configured.

## Architecture

- **Three pipeline stages, each a job in `jobs/`**, wired into `main.py` via APScheduler intervals and also run once on startup:
  - `jobs/fetch_messages.py` (`run_fetch_job`) — scrapes channels, persists raw messages.
  - `jobs/score_messages.py` (`run_evaluate_job`) — scores unscored messages against user resumes.
  - `jobs/forward_matches.py` (`run_forward_job`) — forwards matches above the score threshold.
  - Note: `main.py` currently has the bot and the evaluate/forward jobs commented out — only fetch runs. Uncomment to enable the full pipeline.

- **Two distinct Telegram client libraries** — don't mix their APIs:
  - Telethon (`services/telegram_scraper.py`) uses a *user* session (`session_name.session`) to scrape channels.
  - `python-telegram-bot` (`services/bot_handler.py`, `services/forwarding_service.py`) handles bot commands and forwards messages.

- **Lazy-initialized singletons everywhere** — nothing connects at import time. Each uses a `_var = None` + getter pattern; the first call triggers init: `get_session()`/`get_engine()` (`db/engine.py`), `_get_client()` (scraper), the bot getter (`forwarding_service.py`), the OpenAI client (`scoring_service.py`).

- **DB auto-provisions on first use**: `build_engine()` creates the Postgres database if missing and runs `Base.metadata.create_all()` every startup. No migration tool — schema changes come from editing `db/models/` and relying on `create_all` (which does not alter existing tables).

- **Scoring uses the OpenAI Agents SDK** (`agents` / `openai-agents` package), not the raw OpenAI API. Structured output is a Pydantic `ScoringResult`. The endpoint is configured via `llm_api_key`/`llm_base_url` (OpenAI-compatible, supports non-OpenAI providers). The scoring prompt lives in `services/scoring_constants.py`.

- **`telethon_msg_to_model.py`** (repo root) converts raw Telethon `Message` objects into the Pydantic `TelegramMessage` schema; used only by the scraper.

## Layout Conventions

- Business logic → `jobs/`
- External integrations → `services/`
- Persistence: repositories → `db/repos/`, table models → `db/models/`, engine/session → `db/`
- Cross-module data transfer objects → `schemas/` (Pydantic)

## Configuration

All settings load from `.env` via pydantic-settings (`config.py`, `settings` singleton). Every field in `config.py::Settings` is required at import — a missing env var fails startup. Key groups: Telethon auth (`telegram_api_id/hash/phone`), bot (`telegram_bot_token`), `database_url`, `telegram_channels` (comma-separated), LLM (`llm_api_key`, `llm_base_url`, `scoring_model`), scheduler intervals (`*_interval_minutes`), and concurrency/threshold controls (`scoring_batch_size`, `scoring_max_concurrent`, `forward_score_threshold`, `forward_max_concurrent`).

## Security

Never commit `.env`, `session_name.session` (Telethon user session), API keys, or database URLs — these are gitignored.
