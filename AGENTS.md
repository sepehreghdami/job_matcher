# Repository Guidelines

## Project Structure & Module Organization

This is a Python job-matching service that fetches Telegram job posts, scores them against user resumes, and stores evaluations in PostgreSQL.

- `main.py` starts the async scheduler and job runners.
- `config.py` loads required settings from `.env` via Pydantic settings.
- `jobs/` contains scheduled workflows such as fetching, scoring, and forwarding.
- `services/` contains external-service logic for Telegram, OpenAI scoring, and forwarding.
- `db/` contains SQLAlchemy engine setup, models, and repository helpers.
- `schemas/` contains DTO-style Pydantic models used between layers.
- `post_test.py` is an ad hoc WordPress posting script, not a formal test suite.

Keep virtual environments, session files, caches, and local credentials out of source control. Current ignored examples include `scraper_env/`, `__pycache__/`, `.env`, and `session_name.session`.

## Build, Test, and Development Commands

Create and activate a local virtual environment before running the project:

```powershell
python -m venv scraper_env
.\scraper_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the scheduler locally:

```powershell
python main.py
```

Run individual scripts only when their required `.env` values and external credentials are configured:

```powershell
python post_test.py
```

There is no dedicated build step. Database tables are created on startup through `db.engine.build_engine()`.

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation. Name modules and files in `snake_case.py`, functions in `snake_case`, classes and Pydantic models in `PascalCase`, and constants in `UPPER_SNAKE_CASE`.

Keep business flow in `jobs/`, external integrations in `services/`, persistence in `db/repos/`, and database table definitions in `db/models/`. Prefer typed function signatures and Pydantic schemas when data crosses module boundaries.

## Testing Guidelines

No formal test framework is currently configured. When adding tests, use `pytest`, place tests under `tests/`, and name files `test_<module>.py`. Focus coverage on repository behavior, scoring prompt construction, batching, and scheduler job orchestration.

Recommended command after adding tests:

```powershell
pytest
```

Avoid tests that call Telegram, OpenAI, WordPress, or PostgreSQL directly unless explicitly marked as integration tests and configured with safe test credentials.

## Commit & Pull Request Guidelines

Recent history uses placeholder messages such as `dirty commit`; future commits should be more descriptive. Use short imperative subjects, for example `Add scoring batch retry handling` or `Refactor Telegram message repository`.

Pull requests should include a concise summary, configuration changes, database or schema impacts, and test results. Include screenshots only for user-visible UI changes. Never include real `.env` values, Telegram session files, API keys, or application passwords in commits or PR descriptions.

## Security & Configuration Tips

Treat `.env`, `session_name.session`, API keys, database URLs, Telegram credentials, and WordPress app passwords as secrets. Rotate any credential that was committed or shared. Document required environment variable names, but not their values.
