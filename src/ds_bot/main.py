from __future__ import annotations

from ds_bot.config import Settings
from ds_bot.logging import configure_logging


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    print("ds-bot domain core is ready. Discord adapter will be wired next.")


if __name__ == "__main__":
    main()
