"""Step 1 - collect: search YouTube with yt-dlp and rank recent videos by views per day."""

from __future__ import annotations

from datetime import datetime, timezone


def _upload_dt(entry: dict) -> datetime | None:
    if entry.get("timestamp"):
        return datetime.fromtimestamp(entry["timestamp"], tz=timezone.utc)
    if entry.get("upload_date"):
        return datetime.strptime(entry["upload_date"], "%Y%m%d").replace(tzinfo=timezone.utc)
    return None


def rank_candidates(entries: list[dict], now: datetime, days: int, max_duration: float) -> list[dict]:
    """Keep videos uploaded in the last `days` that last at most `max_duration` s; best views per day first.

    Each kept entry gets `age_days` and `views_per_day`. Duplicates (same id) are dropped.
    """
    seen, kept = set(), []
    for e in entries:
        if not e or e.get("id") in seen:
            continue
        seen.add(e.get("id"))
        dt, dur, views = _upload_dt(e), e.get("duration"), e.get("view_count")
        if dt is None or dur is None or views is None or dur > max_duration:
            continue
        age = max((now - dt).total_seconds() / 86400, 1.0)  # at least one day, so new videos don't explode
        if age > days:
            continue
        kept.append({**e, "age_days": round(age, 1), "views_per_day": round(views / age)})
    return sorted(kept, key=lambda e: e["views_per_day"], reverse=True)


def search(query: str, n: int) -> list[dict]:
    """Full metadata for the first `n` YouTube results of `query` (no download).

    Results come in relevance order and include old videos; `rank_candidates` drops those,
    so look at enough results (per_query) to leave some recent ones.
    """
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{query}", download=False) or {}
    return [e for e in info.get("entries") or [] if e]


KEEP = ("id", "title", "webpage_url", "channel", "duration", "view_count", "like_count",
        "comment_count", "upload_date", "timestamp", "tags")


def collect(queries: list[str], per_query: int, days: int, max_duration: float, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    entries = []
    for q in queries:
        for e in search(q, per_query):
            entries.append({**{k: e.get(k) for k in KEEP}, "query": q})
    return rank_candidates(entries, now, days, max_duration)
