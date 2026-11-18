# trend-pattern-report

[Leer en español](README.es.md)

Every week, find the short videos that are taking off in your niche and measure **how they are edited**: how long they are, how often they cut, how fast the first word comes, and what they say in the first 3 seconds. The result is a report plus a `rules.json` you can follow (or feed to an editing tool) to edit your own videos the same way.

It closes a gap no open-source tool covers: trend tools only collect, and auto-editors only edit. This one turns trending videos into editing rules.

## How it works

| Step | What it does | Built on |
|---|---|---|
| 1. Collect | Searches YouTube for your queries, keeps videos from the last N days under 90 s, ranks them by views per day | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| 2. Measure | Downloads each one at low resolution, detects every cut, transcribes the speech with word timings, then deletes the video | [PySceneDetect](https://github.com/Breakthrough/PySceneDetect), [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| 3. Learn | Medians and ranges of every metric become editing rules. Optionally, Claude groups the hooks into hook types and writes the rules in plain words | [Claude API](https://platform.claude.com/docs) (optional) |
| 4. Report | Writes `reports/<year>-W<week>/report.md`, `data.json` and `rules.json` | |

Metrics per video: length, number of cuts, cuts per second, seconds per shot, time of the first cut, words per minute, share of time talking, time of the first word, and the hook text.

## Run it

Needs Python 3.10+. No FFmpeg install needed.

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m trendpattern run --config config.yaml --limit 3 --no-llm
```

Edit `config.yaml` to set your niche (the queries shipped with it are only an example):

```yaml
queries:
  - "cloud computing explained #shorts"
  - "AI tools tips #shorts"
per_query: 25        # search results per query
top_n: 8             # videos to measure
days: 30             # only videos from the last 30 days
max_duration_s: 90
whisper_model: tiny  # tiny / base / small
use_llm: true
```

YouTube search returns results by relevance, and many are old. The tool drops anything outside the `days` window, so if a report has few videos, raise `per_query` or make the queries more specific.

### The optional Claude step

With `ANTHROPIC_API_KEY` set, step 3 also asks Claude (`claude-opus-5-5`) to name the hook types and write the rules in plain words, using only the measured numbers. Without a key, or with `--no-llm`, the report still has every number and the rule table.

## Weekly run

YouTube blocks GitHub-hosted runners ("Sign in to confirm you're not a bot"), so the weekly report for this repo runs every Monday on a self-hosted runner kept in a separate private repository, and commits the result to `reports/`. Keeping that runner out of this public repo means pull requests from strangers can never run code on that machine.

In this repo, `.github/workflows/weekly.yml` runs the tests on every push and pull request. Its report job can still be started by hand from the Actions tab (with `ANTHROPIC_API_KEY` as a repository secret for the Claude step), but expect YouTube to block it there.

To run it on your own schedule, use cron, Windows Task Scheduler, or a self-hosted runner in a private repo that runs `python -m trendpattern run` in a checkout of this one.

## Responsible use

- Videos are downloaded only to measure them and deleted right after. The report keeps links, public metadata and derived numbers; no video is redistributed.
- Respect each platform's terms of service and keep the number of requests small (the defaults look at about 50 search results and download 8 short videos a week).
- The rules describe what is common among trending videos, not what causes views. Check them against your own retention data.

## Tests

```bash
python -m pytest -q
```

## License

MIT
