"""Step 4 - report: write report.md, data.json and rules.json for the week."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LABELS = {
    "duration_s": "Length (s)", "n_cuts": "Cuts", "cuts_per_sec": "Cuts per second", "avg_shot_s": "Seconds per shot",
    "first_cut_s": "First cut at (s)", "wpm": "Words per minute", "talk_ratio": "Share of time talking",
    "time_to_first_word_s": "First word at (s)",
}
RULE_LABELS = {
    "target_duration_s": "Target length", "cut_every_s": "Cut every", "first_cut_by_s": "First cut by",
    "speech_starts_by_s": "Start talking by", "words_per_minute": "Speaking pace (wpm)", "talk_ratio": "Share of time talking",
}


def week_id(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def _fmt(v, unit=""):
    return "–" if v is None else f"{v}{unit}"


def _md_escape(s: str | None) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(week: str, queries: list[str], videos: list[dict], result: dict) -> str:
    measured = [v for v in videos if v.get("metrics")]
    lines = [f"# Trend pattern report · {week}", "",
             f"Queries: {', '.join(f'`{q}`' for q in queries)}  ",
             f"Videos measured: {len(measured)} of {len(videos)} selected", ""]

    lines += ["## Editing rules", "", "| Rule | Value |", "|---|---|"]
    units = {"target_duration_s": " s", "cut_every_s": " s", "first_cut_by_s": " s", "speech_starts_by_s": " s"}
    for k, label in RULE_LABELS.items():
        lines.append(f"| {label} | {_fmt(result['rules'].get(k), units.get(k, ''))} |")
    lines.append("")

    ins = result.get("insights")
    if ins:
        lines += ["## Hook types", ""]
        for h in ins.get("hook_types", []):
            lines.append(f"- **{h['name']}** ({len(h.get('video_ids', []))} videos): {h['description']}")
        lines += ["", "## Patterns", ""] + [f"- {p}" for p in ins.get("patterns", [])]
        lines += ["", "## Rules in plain words", ""] + [f"- {r}" for r in ins.get("editing_rules", [])] + [""]
    else:
        lines += ["_Hook types and written rules need the Claude step (credentials not found or turned off)._", ""]

    lines += ["## Numbers", "", "| Metric | p25 | Median | p75 |", "|---|---|---|---|"]
    for m, s in result["stats"].items():
        lines.append(f"| {LABELS[m]} | {_fmt(s['p25'])} | {_fmt(s['median'])} | {_fmt(s['p75'])} |")
    lines.append("")

    lines += ["## Videos", "", "| # | Video | Views/day | Length | Cuts/s | First word | Hook |", "|---|---|---|---|---|---|---|"]
    for i, v in enumerate(videos, 1):
        m = v.get("metrics") or {}
        title = _md_escape(v.get("title"))[:70]
        hook = _md_escape(m.get("hook_text") or v.get("error", ""))[:80]
        lines.append(f"| {i} | [{title}]({v.get('webpage_url')}) | {v.get('views_per_day')} | {_fmt(m.get('duration_s'), ' s')} "
                     f"| {_fmt(m.get('cuts_per_sec'))} | {_fmt(m.get('time_to_first_word_s'), ' s')} | {hook} |")
    lines += ["", "Videos are measured and deleted; this report keeps only links, public metadata and derived numbers.", ""]
    return "\n".join(lines)


def write_report(folder: Path, week: str, queries: list[str], videos: list[dict], result: dict) -> Path:
    out = folder / week
    out.mkdir(parents=True, exist_ok=True)
    (out / "data.json").write_text(json.dumps({"week": week, "queries": queries, "videos": videos, **result},
                                              ensure_ascii=False, indent=2), encoding="utf-8")
    rules = {"week": week, "rules": result["rules"],
             "editing_rules": (result.get("insights") or {}).get("editing_rules", [])}
    (out / "rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render_markdown(week, queries, videos, result), encoding="utf-8")
    return out
