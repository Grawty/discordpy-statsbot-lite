from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore

logger = logging.getLogger(__name__)


def format_number(value: int, compact: bool = False) -> str:
    if not compact:
        return f"{value:,}".replace(",", ".")

    # isteğe göre farklı kısaltmalar eklenebilir
    if value >= 1_000_000_000:
        val = f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        val = f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        val = f"{value / 1_000:.1f}K"
    else:
        return str(value)

    return val.replace(".0B", "B").replace(".0M", "M").replace(".0K", "K")


@dataclass
class YouTubeStats:
    subscribers: int
    views: int
    video_count: int
    channel_title: str
    latest_video_title: Optional[str] = None
    formatted_subscribers: str = "0"
    formatted_views: str = "0"


class YouTubeClient:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(
        self,
        api_key: str,
        channel_id: str,
        session: aiohttp.ClientSession,
        cache_ttl: int = 300,
        compact_numbers: bool = False,
    ) -> None:
        self.api_key = api_key
        self.channel_id = channel_id
        self.session = session
        self.cache_ttl = cache_ttl
        self.compact_numbers = compact_numbers

        self._cached_stats: Optional[YouTubeStats] = None
        self._last_fetch_time: float = 0.0
        self._uploads_playlist_id: Optional[str] = None

    async def get_stats(self, force_refresh: bool = False) -> Optional[YouTubeStats]:
        now = time.monotonic()
        if (
            not force_refresh
            and self._cached_stats is not None
            and (now - self._last_fetch_time) < self.cache_ttl
        ):
            return self._cached_stats

        try:
            stats = await self._fetch_from_api()
            if stats:
                self._cached_stats = stats
                self._last_fetch_time = now
                return stats
        except Exception as e:
            logger.error(f"YouTube verisi çekilemedi: {e}")

        return self._cached_stats

    async def _fetch_from_api(self) -> Optional[YouTubeStats]:
        params = {
            "part": "statistics,contentDetails,snippet",
            "id": self.channel_id,
            "key": self.api_key,
        }

        async with self.session.get(f"{self.BASE_URL}/channels", params=params) as resp:
            if resp.status != 200:
                logger.error(f"YouTube API hatası ({resp.status}): {await resp.text()}")
                return None

            data = await resp.json()
            items = data.get("items", [])
            if not items:
                logger.warning(f"Kanal bulunamadı: {self.channel_id}")
                return None

            channel_item = items[0]
            stats_raw = channel_item.get("statistics", {})
            snippet = channel_item.get("snippet", {})
            content_details = channel_item.get("contentDetails", {})

            # son videoyu arama (search) yerine uploads listesinden çekmek 100 kota yerine 1 kota harcar
            self._uploads_playlist_id = content_details.get("relatedPlaylists", {}).get("uploads")

            subscribers = int(stats_raw.get("subscriberCount", 0))
            views = int(stats_raw.get("viewCount", 0))
            video_count = int(stats_raw.get("videoCount", 0))
            channel_title = snippet.get("title", "")

        latest_video_title = await self._fetch_latest_video_title()

        return YouTubeStats(
            subscribers=subscribers,
            views=views,
            video_count=video_count,
            channel_title=channel_title,
            latest_video_title=latest_video_title,
            formatted_subscribers=format_number(
                subscribers, compact=self.compact_numbers
            ),
            formatted_views=format_number(views, compact=self.compact_numbers),
        )

    async def _fetch_latest_video_title(self) -> Optional[str]:
        playlist_id = self._uploads_playlist_id
        if not playlist_id:
            # standart UC... kanal id'sinin 2. harfi U yapılarak uploads listesi elde edilebilir
            if len(self.channel_id) > 2 and self.channel_id.startswith("UC"):
                playlist_id = "UU" + self.channel_id[2:]
            else:
                return None

        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 1,
            "key": self.api_key,
        }

        try:
            async with self.session.get(f"{self.BASE_URL}/playlistItems", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    if items:
                        return items[0]["snippet"].get("title")
        except Exception as e:
            logger.warning(f"Son video başlığı alınamadı: {e}")

        return None
