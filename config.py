from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    discord_token: str
    youtube_api_key: str
    youtube_channel_id: str
    voice_channel_id: Optional[int]
    voice_connect: bool = True
    voice_channel_template: str = "YouTube: {subscribers} ♥"
    channel_update_interval: int = 600
    presence_interval: int = 25
    stats_cache_ttl: int = 300
    compact_numbers: bool = False

    @classmethod
    def load(cls) -> Config:
        if load_dotenv is not None:
            load_dotenv()

        token = os.getenv("TOKEN", "").strip()
        if not token or token == "your_discord_bot_token":
            raise ValueError(".env dosyasında TOKEN bulunamadı.")

        yt_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if not yt_key or yt_key == "your_youtube_api_key":
            raise ValueError(".env dosyasında YOUTUBE_API_KEY bulunamadı.")

        yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
        if not yt_channel_id or yt_channel_id == "your_youtube_channel_id":
            raise ValueError(".env dosyasında YOUTUBE_CHANNEL_ID bulunamadı.")

        raw_voice_id = os.getenv("VOICE_CHANNEL_ID", "").strip()
        voice_channel_id = None
        if raw_voice_id and raw_voice_id != "your_voice_channel_id":
            try:
                voice_channel_id = int(raw_voice_id)
            except ValueError:
                raise ValueError(f"Geçersiz VOICE_CHANNEL_ID: {raw_voice_id}")

        # discord ratelimit yememek için kanal adı güncellemesini en az 300s (5 dk) tutun
        channel_update_interval = _parse_int(
            os.getenv("CHANNEL_UPDATE_INTERVAL"), default=600, min_value=300
        )
        presence_interval = _parse_int(
            os.getenv("PRESENCE_INTERVAL"), default=25, min_value=15
        )
        stats_cache_ttl = _parse_int(
            os.getenv("STATS_CACHE_TTL"), default=300, min_value=60
        )

        compact_numbers = os.getenv("COMPACT_NUMBERS", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        voice_connect = os.getenv("VOICE_CONNECT", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        voice_channel_template = os.getenv(
            "VOICE_CHANNEL_TEMPLATE", "YouTube: {subscribers} ♥"
        )

        return cls(
            discord_token=token,
            youtube_api_key=yt_key,
            youtube_channel_id=yt_channel_id,
            voice_channel_id=voice_channel_id,
            voice_connect=voice_connect,
            voice_channel_template=voice_channel_template,
            channel_update_interval=channel_update_interval,
            presence_interval=presence_interval,
            stats_cache_ttl=stats_cache_ttl,
            compact_numbers=compact_numbers,
        )


def _parse_int(value: Optional[str], default: int, min_value: int) -> int:
    if not value or not value.strip():
        return default
    try:
        return max(min_value, int(value.strip()))
    except ValueError:
        return default
