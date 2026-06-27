"""Southern-dialect text-to-speech via FPT.AI, with a local file cache.

FPT.AI returns an async URL the first time you request synthesis; we fetch the
resulting mp3 once and store it under ``MEDIA_ROOT/audio_cache`` keyed by a
hash of (voice, text). Subsequent requests are served straight from disk, so
we only ever hit the API once per phrase.

If no ``FPT_API_KEY`` is configured, ``audio_path`` returns ``None`` and the
UI simply hides the play button — the app stays fully usable text/IPA-only.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests
from django.conf import settings

_TTS_ENDPOINT = "https://api.fpt.ai/hmi/tts/v5"


def _cache_path(text: str) -> Path:
    voice = settings.FPT_VOICE
    digest = hashlib.sha1(f"{voice}:{text}".encode("utf-8")).hexdigest()[:16]
    return Path(settings.AUDIO_CACHE_DIR) / f"{voice}-{digest}.mp3"


def is_enabled() -> bool:
    return bool(settings.FPT_API_KEY)


def audio_path(text: str) -> Path | None:
    """Return a local mp3 path for ``text``, synthesizing+caching if needed.

    Returns ``None`` when TTS is disabled or synthesis fails, so callers can
    degrade gracefully to text/IPA only.
    """
    if not is_enabled():
        return None

    path = _cache_path(text)
    if path.exists():
        return path

    try:
        return _synthesize(text, path)
    except (requests.RequestException, ValueError):
        return None


def _synthesize(text: str, dest: Path) -> Path | None:
    headers = {
        "api-key": settings.FPT_API_KEY,
        "voice": settings.FPT_VOICE,  # Southern voice, e.g. 'lannhi'
        "speed": "0",
    }
    resp = requests.post(_TTS_ENDPOINT, data=text.encode("utf-8"),
                         headers=headers, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    async_url = payload.get("async")
    if not async_url:
        raise ValueError(f"FPT.AI returned no audio url: {payload}")

    # The mp3 is generated a beat after the request; poll briefly for it.
    dest.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(10):
        audio = requests.get(async_url, timeout=15)
        if audio.status_code == 200 and audio.content[:2] != b"<!":
            dest.write_bytes(audio.content)
            return dest
        time.sleep(0.5)
    raise ValueError("FPT.AI audio not ready after polling")
