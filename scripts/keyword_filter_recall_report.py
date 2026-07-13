"""
Keyword-filter recall check.

Measures whether the keyword pre-filter (services/keyword_matcher.py) risks
silently dropping real matches, using historical ground truth instead of new
LLM calls: take every message_evaluations row that already scored >= a given
threshold (i.e. messages the scoring LLM itself confirmed were real matches,
back when every message got scored), look up that message's text, and check
whether the keyword filter — using the user's *current* keywords — would
have let it through or filtered it out.

The fewer of these known-good matches get filtered out, the more confidence
we have that the filter isn't losing real matches. Zero new LLM cost: this
only reuses evaluations already paid for.

Usage:
    source env-scrapper/bin/activate
    python -m scripts.keyword_filter_recall_report
    python -m scripts.keyword_filter_recall_report --min-score 7 --min-keyword-count 2
    python -m scripts.keyword_filter_recall_report --user-id 18 --show-dropped

Caveats:
- Only covers messages that existed before the filter (i.e. were scored
  under the old "score everything" pipeline) — it's a backward-looking
  recall check, not a live guarantee for future message text.
- message_evaluations doesn't record which scoring_model produced a score,
  so recall can't currently be broken down by model — only by min-score and
  min-keyword-count.
"""

import argparse

from db.engine import get_session
from db.repos.evaluations import get_evaluations
from db.repos.messages import get_messages
from db.repos.user import get_users
from services.keyword_matcher import matches_keywords
from config import settings


def run_report(min_score: float, min_keyword_count: int, user_id: int | None, show_dropped: bool):
    with get_session() as session:
        high_score_evals = get_evaluations(session, score_min=min_score, user_id=user_id)

        by_user: dict[int, list] = {}
        for e in high_score_evals:
            by_user.setdefault(e.user_id, []).append(e)

        users = get_users(session, user_ids=list(by_user.keys()))
        user_map = {u.user_id: u for u in users}

        all_message_pks = list({e.message_pk for e in high_score_evals})
        messages = get_messages(session, pks=all_message_pks)
        message_map = {m.pk: m for m in messages}

    print(f"Keyword-filter recall check (min_score={min_score}, min_keyword_count={min_keyword_count})")
    print(f"Historical known-good matches (score >= {min_score}): {len(high_score_evals)}")
    print()

    total_kept = 0
    total_dropped = 0
    total_missing_message = 0
    total_no_keywords = 0

    for uid, evals in sorted(by_user.items()):
        user = user_map.get(uid)
        if not user or not user.keywords:
            total_no_keywords += len(evals)
            print(f"user_id={uid}: SKIPPED — no keywords stored for this user ({len(evals)} evaluations ignored)")
            continue

        kept, dropped, missing = [], [], 0
        for e in evals:
            msg = message_map.get(e.message_pk)
            if msg is None:
                missing += 1
                continue
            if matches_keywords(msg.text or "", user.keywords, min_keyword_count):
                kept.append((e, msg))
            else:
                dropped.append((e, msg))

        total_kept += len(kept)
        total_dropped += len(dropped)
        total_missing_message += missing

        n = len(kept) + len(dropped)
        recall_pct = (100.0 * len(kept) / n) if n else float("nan")
        print(
            f"user_id={uid}: {n} known-good matches -> {len(kept)} kept, {len(dropped)} would be dropped "
            f"(recall={recall_pct:.1f}%, {len(user.keywords)} keywords)"
            + (f", {missing} messages no longer found" if missing else "")
        )

        if show_dropped and dropped:
            print(f"  Dropped matches for user_id={uid}:")
            for e, msg in sorted(dropped, key=lambda pair: -pair[0].score):
                snippet = (msg.text or "").strip().replace("\n", " ")[:120]
                print(f"    score={e.score:.1f}  message_pk={e.message_pk}  text=\"{snippet}...\"")

    print()
    total_known_good = total_kept + total_dropped
    overall_recall = (100.0 * total_kept / total_known_good) if total_known_good else float("nan")
    print(
        f"OVERALL: {total_known_good} known-good matches evaluated -> "
        f"{total_kept} kept, {total_dropped} would be silently dropped -> recall={overall_recall:.1f}%"
    )
    if total_no_keywords:
        print(f"  ({total_no_keywords} evaluations skipped — user has no stored keywords)")
    if total_missing_message:
        print(f"  ({total_missing_message} evaluations skipped — message row no longer exists)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--min-score", type=float, default=settings.forward_score_threshold,
        help=f"Treat evaluations with score >= this as known-good matches (default: {settings.forward_score_threshold}, from FORWARD_SCORE_THRESHOLD)",
    )
    parser.add_argument(
        "--min-keyword-count", type=int, default=settings.keyword_match_min_count,
        help=f"min_count to test the keyword filter with (default: {settings.keyword_match_min_count}, from KEYWORD_MATCH_MIN_COUNT)",
    )
    parser.add_argument("--user-id", type=int, default=None, help="Restrict the check to a single user_id")
    parser.add_argument(
        "--show-dropped", action="store_true",
        help="Print the actual text of matches that would be dropped, for manual inspection",
    )
    args = parser.parse_args()

    run_report(
        min_score=args.min_score,
        min_keyword_count=args.min_keyword_count,
        user_id=args.user_id,
        show_dropped=args.show_dropped,
    )


if __name__ == "__main__":
    main()
