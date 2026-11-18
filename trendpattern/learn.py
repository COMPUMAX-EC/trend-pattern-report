"""Step 3 - learn: turn the measured videos into an editing pattern and rules.

The numbers always come from the measurements (rule-based). When Claude credentials are
available, Claude also names the hook types and writes the rules in plain words.
"""

from __future__ import annotations

import json
import statistics

METRICS = ("duration_s", "n_cuts", "cuts_per_sec", "avg_shot_s", "first_cut_s", "wpm", "talk_ratio", "time_to_first_word_s")


def _quantiles(values: list[float]) -> dict:
    v = sorted(values)
    if not v:
        return {"n": 0, "p25": None, "median": None, "p75": None}
    if len(v) == 1:
        return {"n": 1, "p25": v[0], "median": v[0], "p75": v[0]}
    q = statistics.quantiles(v, n=4, method="inclusive")
    return {"n": len(v), "p25": round(q[0], 2), "median": round(statistics.median(v), 2), "p75": round(q[2], 2)}


def aggregate(videos: list[dict]) -> dict:
    """p25 / median / p75 of each metric over the measured videos (missing values skipped)."""
    stats = {}
    for m in METRICS:
        stats[m] = _quantiles([v["metrics"][m] for v in videos if v.get("metrics", {}).get(m) is not None])
    return stats


def rules_from_stats(stats: dict) -> dict:
    """Editing rules a person (or an editing tool) can apply, taken straight from the medians."""
    def med(m):
        return stats.get(m, {}).get("median")

    return {
        "target_duration_s": med("duration_s"),
        "cut_every_s": med("avg_shot_s"),
        "first_cut_by_s": med("first_cut_s"),
        "speech_starts_by_s": med("time_to_first_word_s"),
        "words_per_minute": med("wpm"),
        "talk_ratio": med("talk_ratio"),
        "source": "medians of measured videos",
    }


# ---------- Optional Claude step ----------

MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "hook_types": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "video_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "description", "video_ids"],
                "additionalProperties": False,
            },
        },
        "patterns": {"type": "array", "items": {"type": "string"}},
        "editing_rules": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["hook_types", "patterns", "editing_rules"],
    "additionalProperties": False,
}

SYSTEM = (
    "You analyze how trending short videos in one niche are edited, for a creator who wants to edit "
    "their own videos the same way. You get each video's title, hook (the words said in the first 3 seconds) "
    "and measured editing numbers, plus the medians. Group the hooks into a few named hook types. "
    "List patterns you can support with the data, and editing rules a person can follow, using the "
    "measured numbers. Do not invent numbers that are not in the data. If the sample is too small to "
    "support a claim, say so in the pattern instead of guessing."
)


def _prompt(videos: list[dict], stats: dict) -> str:
    rows = [{"id": v["id"], "title": v.get("title"), "views_per_day": v.get("views_per_day"),
             "hook": v["metrics"].get("hook_text"), **{m: v["metrics"].get(m) for m in METRICS}} for v in videos]
    return json.dumps({"videos": rows, "medians": {m: s["median"] for m, s in stats.items()}}, ensure_ascii=False, indent=1)


def llm_insights(videos: list[dict], stats: dict) -> dict | None:
    """Hook types, patterns and rules from Claude, or None when unavailable (no credentials, error, refusal)."""
    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            system=SYSTEM,
            messages=[{"role": "user", "content": _prompt(videos, stats)}],
        )
    except Exception as exc:  # no credentials, network, API error: the report still works without this step
        print(f"  Claude step skipped: {type(exc).__name__}: {exc}")
        return None
    if response.stop_reason == "refusal":
        print("  Claude step skipped: the request was declined")
        return None
    text = next((b.text for b in response.content if b.type == "text"), None)
    try:
        return json.loads(text) if text else None
    except json.JSONDecodeError:
        print("  Claude step skipped: response was not valid JSON")
        return None


def learn(videos: list[dict], use_llm: bool) -> dict:
    measured = [v for v in videos if v.get("metrics")]
    stats = aggregate(measured)
    return {
        "stats": stats,
        "rules": rules_from_stats(stats),
        "insights": llm_insights(measured, stats) if use_llm and measured else None,
    }
