from datetime import datetime, timedelta, timezone

from trendpattern.collect import rank_candidates
from trendpattern.learn import aggregate, rules_from_stats
from trendpattern.measure import compute_metrics
from trendpattern.report import render_markdown, week_id

NOW = datetime(2026, 11, 18, tzinfo=timezone.utc)


def entry(id, days_ago, views, duration=40):
    return {"id": id, "timestamp": (NOW - timedelta(days=days_ago)).timestamp(), "view_count": views, "duration": duration}


def test_rank_by_views_per_day_and_filters():
    entries = [
        entry("old", 30, 1_000_000),          # too old
        entry("long", 2, 900_000, 600),       # too long
        entry("slow", 10, 100_000),           # 10k/day
        entry("fast", 2, 100_000),            # 50k/day
        entry("fast", 2, 100_000),            # duplicate
        {"id": "nodate", "view_count": 5, "duration": 10},
    ]
    ranked = rank_candidates(entries, NOW, days=14, max_duration=90)
    assert [e["id"] for e in ranked] == ["fast", "slow"]
    assert ranked[0]["views_per_day"] == 50_000


def test_new_video_counts_at_least_one_day():
    ranked = rank_candidates([entry("new", 0.1, 3_000)], NOW, days=14, max_duration=90)
    assert ranked[0]["views_per_day"] == 3_000


def test_upload_date_string_is_accepted():
    e = {"id": "x", "upload_date": "20261116", "view_count": 2_000, "duration": 30}
    assert rank_candidates([e], NOW, 14, 90)[0]["views_per_day"] == 1_000


def test_compute_metrics():
    words = [(0.4, 0.7, " Stop"), (0.7, 1.0, " paying"), (1.0, 1.4, " for"), (3.5, 3.9, " cloud")]
    m = compute_metrics(20.0, [2.0, 5.0, 0.0, 25.0], words, "en")
    assert m["n_cuts"] == 2                      # 0 and 25 are outside the video
    assert m["avg_shot_s"] == round(20 / 3, 2)
    assert m["first_cut_s"] == 2.0
    assert m["time_to_first_word_s"] == 0.4
    assert m["hook_text"] == "Stop paying for"   # only words starting before 3 s
    assert m["wpm"] == 12
    assert m["language"] == "en"


def test_compute_metrics_no_cuts_no_speech():
    m = compute_metrics(10.0, [], [])
    assert m["n_cuts"] == 0 and m["first_cut_s"] is None
    assert m["time_to_first_word_s"] is None and m["hook_text"] == ""


def test_aggregate_and_rules():
    videos = [{"metrics": compute_metrics(d, cuts, [(t, t + 0.3, "hi")])}
              for d, cuts, t in [(30, [1, 2, 3], 0.2), (40, [2, 4], 0.5), (50, [1.5], 1.0)]]
    videos.append({"error": "download failed"})
    stats = aggregate(videos)
    assert stats["duration_s"] == {"n": 3, "p25": 35.0, "median": 40.0, "p75": 45.0}
    rules = rules_from_stats(stats)
    assert rules["target_duration_s"] == 40.0
    assert rules["first_cut_by_s"] == 1.5
    assert rules["speech_starts_by_s"] == 0.5


def test_report_renders_without_insights():
    videos = [{"id": "a", "title": "A | B", "webpage_url": "https://youtu.be/a", "views_per_day": 10,
               "metrics": compute_metrics(30, [3], [(0.2, 0.5, "Hey")])}]
    stats = aggregate(videos)
    md = render_markdown("2026-W47", ["q"], videos, {"stats": stats, "rules": rules_from_stats(stats), "insights": None})
    assert "Trend pattern report · 2026-W47" in md
    assert "A \\| B" in md
    assert week_id(NOW) == "2026-W47"
