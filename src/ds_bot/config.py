from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    discord_guild_id: int | None
    host_role_id: int | None
    control_channel_id: int | None
    zombie_channel_id: int | None
    database_url: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            discord_token=os.getenv("DISCORD_TOKEN", ""),
            discord_guild_id=_optional_int("DISCORD_GUILD_ID"),
            host_role_id=_optional_int("HOST_ROLE_ID"),
            control_channel_id=_optional_int("CONTROL_CHANNEL_ID"),
            zombie_channel_id=_optional_int("ZOMBIE_CHANNEL_ID"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/ds_bot.sqlite3"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


def _optional_int(name: str) -> int | None:
    raw = os.getenv(name)
    if not raw:
        return None
    return int(raw)
