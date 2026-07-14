# scripts/run_recall_experiment.py
"""
Full with/without-filter comparison across the 20 mock users
(scripts/mock_resumes.py, scripts/setup_mock_users.py) against every message
from a fixed recent window.

Scores every message in the window for every user EXACTLY ONCE (not twice) —
this single "ground truth" pass answers both questions at once:
  - "without filter" performance = every message's real score
  - "with filter" performance = the subset of those real scores whose message
    also passes services.keyword_matcher.filter_messages_by_keywords

Checkpointed and resumable: every completed batch (success or permanent
failure) is appended to a JSONL file immediately, not held in memory until
the end. If the run is interrupted (quota exhaustion, crash, ctrl-C), rerun
the same command — it skips everything already done and only scores the
remainder. The message window is frozen into a manifest file on first run so
resumed runs use the exact same messages rather than a drifting "last N
days" window.

Usage:
    source env-scrapper/bin/activate
    python -m scripts.run_recall_experiment --days 5 --concurrency 8
    # if interrupted (e.g. quota ran out), just rerun the same command to resume
    python -m scripts.run_recall_experiment --days 5 --concurrency 8
    # to start over from scratch:
    python -m scripts.run_recall_experiment --days 5 --concurrency 8 --reset
"""

import argparse
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from logging_config import setup_logging

setup_logging()

from db.engine import get_session
from db.models.user import User
from db.repos.messages import get_messages
from schemas.user import UserDto
from services.scoring_service import _score_batch
from config import settings

logger = logging.getLogger(__name__)

MOCK_CHAT_ID_BASE = 900000
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [5, 15, 45]

MANIFEST_PATH = "scripts/recall_experiment_manifest.json"
CHECKPOINT_PATH = "scripts/recall_experiment_checkpoint.jsonl"


def _load_or_create_manifest(days: int, batch_size: int) -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        logger.info(
            "[experiment] reusing existing manifest (%d messages, frozen from a previous run)",
            len(manifest["message_pks"]),
        )
        return manifest

    date_from = datetime.now(timezone.utc) - timedelta(days=days)
    with get_session() as session:
        messages = [m for m in get_messages(session, date_from=date_from) if m.text]
    messages.sort(key=lambda m: m.pk)  # deterministic batch boundaries

    message_pks = [m.pk for m in messages]
    batches = [message_pks[i:i + batch_size] for i in range(0, len(message_pks), batch_size)]

    manifest = {"days": days, "batch_size": batch_size, "message_pks": message_pks, "batches": batches}
    # Write to a temp file then rename — rename is atomic, so a crash mid-write
    # can never leave a half-written, unparseable manifest on disk.
    tmp_path = MANIFEST_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(manifest, f)
    os.replace(tmp_path, MANIFEST_PATH)
    logger.info("[experiment] created new manifest: %d messages, %d batches", len(message_pks), len(batches))
    return manifest


def _load_completed() -> set:
    """(chat_id, batch_index) pairs that already succeeded — safe to skip on resume."""
    completed = set()
    if not os.path.exists(CHECKPOINT_PATH):
        return completed
    with open(CHECKPOINT_PATH) as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # Only expected on the last line, if the process was hard-killed
                # mid-write (e.g. power loss, SIGKILL) — that batch simply
                # wasn't checkpointed and will be retried below, no data lost.
                logger.warning(
                    "[experiment] skipping unparseable checkpoint line %d (likely a partial write from a hard interrupt)",
                    line_num,
                )
                continue
            if rec["ok"]:
                completed.add((rec["chat_id"], rec["batch_index"]))
    return completed


class QuotaExhausted(Exception):
    """Raised when the LLM gateway reports the account is out of funds — not
    worth retrying, and not worth attempting any further batches this run."""


def _is_quota_error(e: Exception) -> bool:
    msg = str(e).lower()
    return "insufficient_user_quota" in msg or "insufficient user quota" in msg


async def _score_batch_with_retry(
    user: UserDto, batch_index: int, batch_msgs: list, sem: asyncio.Semaphore, stop_flag: dict,
) -> dict:
    if stop_flag["hit"]:
        # Quota already confirmed exhausted by another task — don't even try,
        # just record as not-done (not a real failure) so it's retried, not
        # skipped, next time. Keeps a dead account from burning through
        # hundreds of doomed retries one batch at a time.
        return {"chat_id": user.telegram_chat_id, "batch_index": batch_index, "ok": False, "skipped": True}

    async with sem:
        if stop_flag["hit"]:
            return {"chat_id": user.telegram_chat_id, "batch_index": batch_index, "ok": False, "skipped": True}

        last_error = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                evals = await _score_batch(user, batch_msgs)
                return {
                    "chat_id": user.telegram_chat_id,
                    "batch_index": batch_index,
                    "ok": True,
                    "evals": [e.model_dump(mode="json") for e in evals],
                }
            except Exception as e:
                last_error = e
                if _is_quota_error(e):
                    logger.error(
                        "[experiment] LLM quota exhausted — stopping new batches (top up and rerun to resume). "
                        "First seen on user=%s batch=%d", user.telegram_chat_id, batch_index,
                    )
                    stop_flag["hit"] = True
                    break  # no point retrying a dead quota
                if attempt < RETRY_ATTEMPTS - 1:
                    wait = RETRY_BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "[experiment] user=%s batch=%d failed (attempt %d/%d): %s — retrying in %ds",
                        user.telegram_chat_id, batch_index, attempt + 1, RETRY_ATTEMPTS, type(e).__name__, wait,
                    )
                    await asyncio.sleep(wait)
        logger.error("[experiment] user=%s batch=%d failed permanently: %s", user.telegram_chat_id, batch_index, last_error)
        return {
            "chat_id": user.telegram_chat_id,
            "batch_index": batch_index,
            "ok": False,
            "message_pks": [m.pk for m in batch_msgs],
            "error": str(last_error),
        }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--reset", action="store_true", help="wipe manifest+checkpoint and start fresh")
    args = parser.parse_args()

    if args.reset:
        for p in (MANIFEST_PATH, CHECKPOINT_PATH):
            if os.path.exists(p):
                os.remove(p)
        logger.info("[experiment] --reset: cleared manifest and checkpoint")

    mock_chat_ids = [MOCK_CHAT_ID_BASE + i for i in range(1, 21)]
    with get_session() as session:
        rows = session.execute(
            select(User).where(User.telegram_chat_id.in_(mock_chat_ids)).order_by(User.telegram_chat_id)
        ).scalars().all()
        users = [UserDto.model_validate(r) for r in rows]

    if len(users) != 20 or any(not u.keywords for u in users):
        raise RuntimeError("Expected 20 mock users, all with keywords. Run scripts.setup_mock_users first.")

    manifest = _load_or_create_manifest(args.days, settings.scoring_batch_size)
    batches_pks = manifest["batches"]

    with get_session() as session:
        all_msgs = get_messages(session, pks=manifest["message_pks"])
    msg_by_pk = {m.pk: m for m in all_msgs}
    batches = [[msg_by_pk[pk] for pk in pks if pk in msg_by_pk] for pks in batches_pks]

    completed = _load_completed()
    logger.info("[experiment] %d/%d (user, batch) pairs already completed — resuming the rest",
                len(completed), len(users) * len(batches))

    todo = [
        (user, i, batch)
        for user in users
        for i, batch in enumerate(batches)
        if (user.telegram_chat_id, i) not in completed
    ]

    if not todo:
        logger.info("[experiment] nothing left to do — all batches already completed. Run scripts.report_recall_experiment.")
        return

    logger.info("[experiment] %d batch calls remaining, concurrency=%d", len(todo), args.concurrency)

    sem = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    stop_flag = {"hit": False}

    async def _run_and_checkpoint(user, batch_index, batch_msgs):
        result = await _score_batch_with_retry(user, batch_index, batch_msgs, sem, stop_flag)
        if result.get("skipped"):
            # Quota was already known-dead when this task got its turn — don't
            # even write a "failed" record; leaving it absent from the
            # checkpoint means it's picked up fresh (not retried-and-failed)
            # next run, and keeps the file from bloating with dead entries.
            return False
        async with write_lock:
            with open(CHECKPOINT_PATH, "a") as f:
                f.write(json.dumps(result) + "\n")
                f.flush()
        return result["ok"]

    t0 = time.perf_counter()
    results = await asyncio.gather(*(_run_and_checkpoint(u, i, b) for u, i, b in todo))
    elapsed = time.perf_counter() - t0

    ok_count = sum(1 for r in results if r)
    logger.info(
        "[experiment] batch of work done in %.1fs (%.1f min): %d/%d ok this run",
        elapsed, elapsed / 60, ok_count, len(todo),
    )
    if stop_flag["hit"]:
        logger.warning("[experiment] stopped early — LLM quota was exhausted. Top up and rerun the same command to resume.")

    total_completed = len(_load_completed())
    total_needed = len(users) * len(batches)
    if total_completed >= total_needed:
        logger.info("[experiment] ALL %d (user, batch) pairs complete. Run scripts.report_recall_experiment next.", total_needed)
    else:
        logger.info(
            "[experiment] %d/%d complete — rerun this same command to continue (e.g. after topping up API quota).",
            total_completed, total_needed,
        )


if __name__ == "__main__":
    asyncio.run(main())
