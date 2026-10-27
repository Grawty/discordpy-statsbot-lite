from __future__ import annotations

import logging
from typing import Optional

import aiohttp
import discord
from discord.ext import tasks

from config import Config
from youtube import YouTubeClient, YouTubeStats

logger = logging.getLogger(__name__)


class StatsBot(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.youtube: Optional[YouTubeClient] = None
        self._presence_step = 0

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.youtube = YouTubeClient(
            api_key=self.config.youtube_api_key,
            channel_id=self.config.youtube_channel_id,
            session=self.session,
            cache_ttl=self.config.stats_cache_ttl,
            compact_numbers=self.config.compact_numbers,
        )

        self.channel_updater_task.change_interval(
            seconds=self.config.channel_update_interval
        )
        self.presence_updater_task.change_interval(
            seconds=self.config.presence_interval
        )

        self.channel_updater_task.start()
        self.presence_updater_task.start()

    async def close(self) -> None:
        if self.channel_updater_task.is_running():
            self.channel_updater_task.cancel()
        if self.presence_updater_task.is_running():
            self.presence_updater_task.cancel()

        if self.session and not self.session.closed:
            await self.session.close()

        await super().close()

    async def on_ready(self) -> None:
        if not self.user:
            return

        logger.info(f"Giriş yapıldı: {self.user} (Sunucu sayısı: {len(self.guilds)})")

        if self.config.voice_connect and self.config.voice_channel_id:
            await self._ensure_voice_connection()

    async def _ensure_voice_connection(self) -> None:
        if not self.config.voice_channel_id:
            return

        channel = self.get_channel(self.config.voice_channel_id)
        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            return

        try:
            voice_client = channel.guild.voice_client
            if voice_client is None:
                await channel.connect(self_deaf=True)
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)
        except Exception as e:
            logger.warning(f"Ses kanalına bağlanamadı: {e}")

    @tasks.loop(seconds=600)
    async def channel_updater_task(self) -> None:
        if not self.config.voice_channel_id or not self.youtube:
            return

        channel = self.get_channel(self.config.voice_channel_id)
        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            return

        stats = await self.youtube.get_stats()
        if not stats:
            return

        new_name = self.config.voice_channel_template.format(
            subscribers=stats.formatted_subscribers,
            views=stats.formatted_views,
            videos=stats.video_count,
            channel=stats.channel_title,
        )

        # ratelimit yememek için isim aynıysa api isteği atma
        if channel.name == new_name:
            return

        try:
            await channel.edit(name=new_name, reason="YouTube istatistik güncellemesi")
            logger.info(f"Kanal adı güncellendi: {new_name}")
        except discord.errors.Forbidden:
            logger.error("Kanalı düzenleme yetkisi eksik (Manage Channels yetkisi verin).")
        except discord.errors.HTTPException as e:
            logger.warning(f"Kanal adı güncellenirken hata: {e}")

    @channel_updater_task.before_loop
    async def before_channel_updater(self) -> None:
        await self.wait_until_ready()

    @tasks.loop(seconds=25)
    async def presence_updater_task(self) -> None:
        if not self.youtube:
            return

        stats: Optional[YouTubeStats] = await self.youtube.get_stats()
        total_members = sum(guild.member_count or 0 for guild in self.guilds)

        # buraya sırayla gösterilmesini istediğin yeni durumları ekleyebilirsin
        activities = [
            discord.Activity(
                type=discord.ActivityType.playing,
                name=f"Discord {total_members:,} üye 🦄".replace(",", "."),
            ),
        ]

        if stats:
            activities.append(
                discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"{stats.formatted_views} görüntülenme 🙌",
                )
            )
            activities.append(
                discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"{stats.formatted_subscribers} abone 🥳",
                )
            )
            if stats.latest_video_title:
                title = stats.latest_video_title
                if len(title) > 60:
                    title = title[:57] + "..."
                activities.append(
                    discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f"En Son: {title}",
                    )
                )

        if not activities:
            return

        activity = activities[self._presence_step % len(activities)]
        self._presence_step += 1

        try:
            await self.change_presence(activity=activity)
        except Exception:
            pass

    @presence_updater_task.before_loop
    async def before_presence_updater(self) -> None:
        await self.wait_until_ready()


if __name__ == "__main__":
    from main import main
    main()
