from __future__ import annotations

from ds_bot.config import Settings
from ds_bot.discord.bot import create_bot
from ds_bot.logging import configure_logging


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required to run the bot.")
    bot = create_bot(settings)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
