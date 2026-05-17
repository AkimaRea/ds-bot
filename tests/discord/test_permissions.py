from __future__ import annotations

import pytest

from ds_bot.discord.permissions import (
    DiscordAccessConfig,
    DiscordContext,
    ensure_host_access,
    ensure_zombie_access,
    resolve_team_id,
)
from ds_bot.domain.errors import InvalidOrderError
from ds_bot.domain.initial_map import create_initial_game


def test_host_access_requires_control_channel_and_role() -> None:
    config = DiscordAccessConfig(
        host_role_id=10,
        control_channel_id=20,
        zombie_channel_id=None,
    )

    ensure_host_access(DiscordContext(1, 20, frozenset({10})), config)

    with pytest.raises(InvalidOrderError):
        ensure_host_access(DiscordContext(1, 21, frozenset({10})), config)
    with pytest.raises(InvalidOrderError):
        ensure_host_access(DiscordContext(1, 20, frozenset({11})), config)


def test_resolve_team_id_uses_channel_and_role() -> None:
    game = create_initial_game(team_discord={1: (101, 201), 2: (102, 202)})

    assert resolve_team_id(game, DiscordContext(1, 201, frozenset({101}))) == 1

    with pytest.raises(InvalidOrderError):
        resolve_team_id(game, DiscordContext(1, 201, frozenset({102})))


def test_zombie_access_requires_zombie_channel() -> None:
    config = DiscordAccessConfig(
        host_role_id=None,
        control_channel_id=None,
        zombie_channel_id=300,
    )

    ensure_zombie_access(DiscordContext(1, 300, frozenset()), config)
    with pytest.raises(InvalidOrderError):
        ensure_zombie_access(DiscordContext(1, 301, frozenset()), config)
