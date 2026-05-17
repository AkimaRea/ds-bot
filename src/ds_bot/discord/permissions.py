from __future__ import annotations

from dataclasses import dataclass

from ds_bot.domain.errors import InvalidOrderError
from ds_bot.domain.models import GameState


@dataclass(frozen=True, slots=True)
class DiscordContext:
    user_id: int
    channel_id: int
    role_ids: frozenset[int]


@dataclass(frozen=True, slots=True)
class DiscordAccessConfig:
    host_role_id: int | None
    control_channel_id: int | None
    zombie_channel_id: int | None


def ensure_host_access(context: DiscordContext, config: DiscordAccessConfig) -> None:
    if config.control_channel_id is not None and context.channel_id != config.control_channel_id:
        raise InvalidOrderError("Host action is allowed only in the control channel.")
    if config.host_role_id is not None and config.host_role_id not in context.role_ids:
        raise InvalidOrderError("User is not a host.")


def resolve_team_id(game: GameState, context: DiscordContext) -> int:
    for team in game.teams.values():
        if team.discord_channel_id is None and team.discord_role_id is None:
            continue
        channel_ok = team.discord_channel_id is None or team.discord_channel_id == context.channel_id
        role_ok = team.discord_role_id is None or team.discord_role_id in context.role_ids
        if channel_ok and role_ok:
            return team.id
    raise InvalidOrderError("User does not belong to a team in this channel.")


def ensure_zombie_access(context: DiscordContext, config: DiscordAccessConfig) -> None:
    if config.zombie_channel_id is not None and context.channel_id != config.zombie_channel_id:
        raise InvalidOrderError("Zombie command is allowed only in the zombie channel.")
