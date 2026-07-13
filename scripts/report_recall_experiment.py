# scripts/report_recall_experiment.py
"""
Analyzes scripts/recall_experiment_checkpoint.jsonl (produced by
scripts/run_recall_experiment.py) and reports, per user and overall:
  - recall: of the messages that scored >= --min-score (real "true matches"
    found by scoring the whole window), what fraction also pass the keyword
    filter (i.e. would NOT have been silently dropped)?
  - cost reduction: batches needed with vs without the filter, for this
    message window.

Works fine on a partially-complete checkpoint (e.g. if the run is still in
progress or was interrupted) — just reports on whatever's done so far and
notes how much of the experiment that represents.

Usage:
    source env-scrapper/bin/activate
    python -m scripts.report_recall_experiment
    python -m scripts.report_recall_experiment --min-score 7 --min-keyword-count 2
"""

import argparse
import json
import math
import os
from collections import defaultdict
from sqlalchemy import select

from db.engine import get_session
from db.models.user import User
from db.repos.messages import get_messages
from schemas.user import UserDto
from services.keyword_matcher import matches_keywords
from config import settings

MOCK_CHAT_ID_BASE = 900000
MANIFEST_PATH = "scripts/recall_experiment_manifest.json"
CHECKPOINT_PATH = "scripts/recall_experiment_checkpoint.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-score", type=float, default=settings.forward_score_threshold)
    parser.add_argument("--min-keyword-count", type=int, default=settings.keyword_match_min_count)
    args = parser.parse_args()

    if not os.path.exists(MANIFEST_PATH) or not os.path.exists(CHECKPOINT_PATH):
        raise SystemExit("No experiment data found — run scripts.run_recall_experiment first.")

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    total_batches_needed = len(manifest["batches"]) * 20

    evals_by_user = defaultdict(list)
    ok_count = 0
    failed_count = 0
    with open(CHECKPOINT_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec["ok"]:
                ok_count += 1
                evals_by_user[rec["chat_id"]].extend(rec["evals"])
            else:
                failed_count += 1

    print(f"Checkpoint: {ok_count}/{total_batches_needed} batches complete "
          f"({100*ok_count/total_batches_needed:.1f}%), {failed_count} permanently failed")
    print(f"Scoring threshold (real match) = {args.min_score}, keyword min_count = {args.min_keyword_count}")
    print()

    mock_chat_ids = [MOCK_CHAT_ID_BASE + i for i in range(1, 21)]
    with get_session() as session:
        rows = session.execute(
            select(User).where(User.telegram_chat_id.in_(mock_chat_ids)).order_by(User.telegram_chat_id)
        ).scalars().all()
        users = {u.telegram_chat_id: UserDto.model_validate(u) for u in rows}

    with get_session() as session:
        all_msgs = get_messages(session, pks=manifest["message_pks"])
    text_by_pk = {m.pk: (m.text or "") for m in all_msgs}

    total_true_matches = 0
    total_kept_true_matches = 0
    total_before_batches = 0
    total_after_batches = 0
    batch_size = manifest["batch_size"]

    rows_out = []
    for chat_id, user in users.items():
        evals = evals_by_user.get(chat_id, [])
        if not evals:
            rows_out.append((user.telegram_username, "no data yet", 0, 0, float("nan"), 0, 0))
            continue

        keywords = user.keywords
        scored_pks = {e["message_pk"] for e in evals}
        true_matches = [e for e in evals if e["score"] is not None and e["score"] >= args.min_score]

        kept_pks = {
            pk for pk in scored_pks
            if matches_keywords(text_by_pk.get(pk, ""), keywords, args.min_keyword_count)
        }
        kept_true = [e for e in true_matches if e["message_pk"] in kept_pks]

        n_true = len(true_matches)
        n_kept_true = len(kept_true)
        n_kept = len(kept_pks)
        n_scored = len(scored_pks)
        recall = (100.0 * n_kept_true / n_true) if n_true else float("nan")

        before_batches = math.ceil(n_scored / batch_size) if n_scored else 0
        after_batches = math.ceil(n_kept / batch_size) if n_kept else 0

        rows_out.append((user.telegram_username, "ok", n_true, n_kept_true, recall, n_kept, n_scored))

        total_true_matches += n_true
        total_kept_true_matches += n_kept_true
        total_before_batches += before_batches
        total_after_batches += after_batches

    print(f"{'User':<16} {'Status':<10} {'TrueMatches':>11} {'Kept':>6} {'Recall':>8} {'KeptTotal':>10} {'Scored':>7}")
    for row in rows_out:
        name, status, *rest = row
        if status != "ok":
            print(f"{name:<16} {status:<10}")
            continue
        n_true, n_kept_true, recall, n_kept, n_scored = rest
        recall_str = f"{recall:.1f}%" if n_true else "n/a"
        print(f"{name:<16} {'ok':<10} {n_true:>11} {n_kept_true:>6} {recall_str:>8} {n_kept:>10} {n_scored:>7}")

    print()
    overall_recall = (100.0 * total_kept_true_matches / total_true_matches) if total_true_matches else float("nan")
    print(f"OVERALL (users with data so far): {total_true_matches} true matches (score>={args.min_score}), "
          f"{total_kept_true_matches} kept by filter -> recall={overall_recall:.1f}%")
    print()
    reduction = 100.0 * (total_before_batches - total_after_batches) / total_before_batches if total_before_batches else 0
    print(f"Batches without filter: {total_before_batches}")
    print(f"Batches with filter:    {total_after_batches}")
    print(f"Batch/cost reduction:   {reduction:.2f}%")


if __name__ == "__main__":
    main()
