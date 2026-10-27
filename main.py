from __future__ import annotations

import logging
import sys

from config import Config
from bot import StatsBot


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def main() -> None:
    setup_logging()
    logger = logging.getLogger("bot")

    try:
        config = Config.load()
    except ValueError as e:
        logger.error(f"Yapılandırma hatası: {e}")
        sys.exit(1)

    bot = StatsBot(config=config)

    try:
        bot.run(config.discord_token, log_handler=None)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
