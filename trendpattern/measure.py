"""Step 2 - measure: how fast a video is cut and how fast it talks.

The video is downloaded at low resolution to a temporary folder, measured, and deleted.
Only the derived numbers and the first words (the hook) are kept.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

HOOK_SECONDS = 3.0
# Shorts usually have no combined video+audio file, and merging needs ffmpeg. So we fetch the two
# streams separately: a small H.264 video (OpenCV can decode it) for cuts, and m4a audio for speech.
VIDEO_FORMAT = "bv[vcodec^=avc1][height<=360][height>=240]/bv[vcodec^=avc1][height<=480]/wv[vcodec^=avc1]/18"
AUDIO_FORMAT = "ba[ext=m4a]/ba/18"


def compute_metrics(duration: float, cut_times: list[float], words: list[tuple[float, float, str]],
                    language: str | None = None) -> dict:
    """Editing and speech metrics from cut times (s) and timed words (start, end, text)."""
    cuts = sorted(t for t in cut_times if 0 < t < duration)
    shots = len(cuts) + 1
    spoken = [w for w in words if w[2].strip()]
    talk_time = sum(max(0.0, e - s) for s, e, _ in spoken)
    hook = " ".join(w[2].strip() for w in spoken if w[0] < HOOK_SECONDS)
    return {
        "duration_s": round(duration, 1),
        "n_cuts": len(cuts),
        "cuts_per_sec": round(len(cuts) / duration, 3) if duration else 0.0,
        "avg_shot_s": round(duration / shots, 2) if duration else 0.0,
        "first_cut_s": round(cuts[0], 2) if cuts else None,
        "words": len(spoken),
        "wpm": round(len(spoken) / duration * 60) if duration else 0,
        "talk_ratio": round(min(talk_time / duration, 1.0), 2) if duration else 0.0,
        "time_to_first_word_s": round(spoken[0][0], 2) if spoken else None,
        "hook_text": hook,
        "language": language,
    }


def download(url: str, folder: Path, fmt: str, name: str) -> Path:
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "format": fmt, "outtmpl": str(folder / f"{name}.%(ext)s")}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))


def detect_cuts(path: Path) -> tuple[float, list[float]]:
    from scenedetect import AdaptiveDetector, detect, open_video

    duration = open_video(str(path)).duration.get_seconds()
    scenes = detect(str(path), AdaptiveDetector())
    return duration, [start.get_seconds() for start, _ in scenes[1:]]


_models: dict = {}


def transcribe(path: Path, model_name: str) -> tuple[list[tuple[float, float, str]], str | None]:
    from faster_whisper import WhisperModel

    if model_name not in _models:
        _models[model_name] = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = _models[model_name].transcribe(str(path), word_timestamps=True, vad_filter=True)
    words = [(w.start, w.end, w.word) for seg in segments for w in (seg.words or [])]
    return words, info.language


def measure(url: str, whisper_model: str = "tiny") -> dict:
    with tempfile.TemporaryDirectory(prefix="trendpattern-", ignore_cleanup_errors=True) as tmp:
        video = download(url, Path(tmp), VIDEO_FORMAT, "video")
        audio = download(url, Path(tmp), AUDIO_FORMAT, "audio")
        duration, cuts = detect_cuts(video)
        words, language = transcribe(audio, whisper_model)
        return compute_metrics(duration, cuts, words, language)
