"""Load the run settings from a YAML file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    queries: list[str]
    per_query: int = 25          # search results to look at per query
    top_n: int = 8               # videos to measure after ranking
    days: int = 30               # only videos uploaded in the last N days
    max_duration_s: int = 90     # Shorts-length videos only
    whisper_model: str = "tiny"  # tiny / base / small: bigger is slower but more accurate
    use_llm: bool = True         # ask Claude to name hook types and write rules, when credentials exist
    reports_dir: str = "reports"
    extra: dict = field(default_factory=dict)


def load_config(path: str | Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not data.get("queries"):
        raise ValueError(f"{path}: 'queries' must list at least one search query")
    known = Config.__dataclass_fields__.keys()
    extra = {k: v for k, v in data.items() if k not in known}
    return Config(**{k: v for k, v in data.items() if k in known}, extra=extra)
