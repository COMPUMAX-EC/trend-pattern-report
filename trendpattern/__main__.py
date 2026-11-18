"""Command line: python -m trendpattern run --config config.yaml [--limit N] [--no-llm]"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .collect import collect
from .config import load_config
from .learn import learn
from .measure import measure
from .report import week_id, write_report


def run(args) -> int:
    cfg = load_config(args.config)
    now = datetime.now(timezone.utc)
    top_n = args.limit or cfg.top_n

    print(f"1/4 Collecting: {len(cfg.queries)} queries x {cfg.per_query} results")
    ranked = collect(cfg.queries, cfg.per_query, cfg.days, cfg.max_duration_s, now)
    videos = ranked[:top_n]
    print(f"    {len(ranked)} recent videos under {cfg.max_duration_s} s; measuring the top {len(videos)}")
    if not videos:
        print("No videos matched. Widen 'days', raise 'per_query' or change the queries.")
        return 1

    print(f"2/4 Measuring (Whisper model: {cfg.whisper_model})")
    for i, v in enumerate(videos, 1):
        print(f"    [{i}/{len(videos)}] {v.get('title', '')[:60]}")
        try:
            v["metrics"] = measure(v["webpage_url"], cfg.whisper_model)
        except Exception as exc:  # one bad video shouldn't stop the report
            v["error"] = f"{type(exc).__name__}: {exc}"[:200]
            print(f"        skipped: {v['error']}")

    print("3/4 Learning the pattern")
    result = learn(videos, use_llm=cfg.use_llm and not args.no_llm)

    out = write_report(Path(cfg.reports_dir), week_id(now), cfg.queries, videos, result)
    print(f"4/4 Report written to {out / 'report.md'}")
    return 0 if any(v.get("metrics") for v in videos) else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="trendpattern", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="collect, measure, learn and write this week's report")
    r.add_argument("--config", default="config.yaml")
    r.add_argument("--limit", type=int, help="measure at most N videos (overrides top_n)")
    r.add_argument("--no-llm", action="store_true", help="skip the Claude step")
    args = p.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
