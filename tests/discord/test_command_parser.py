from __future__ import annotations

import pytest

from ds_bot.discord.buttons import ButtonAction, ButtonId, ensure_fresh_button, parse_button_id
from ds_bot.discord.command_parser import parse_command
from ds_bot.domain.enums import OrderType
from ds_bot.domain.errors import InvalidOrderError


def test_parse_team_commands() -> None:
    attack = parse_command("!attack 50 1 в 8")
    move = parse_command("!move 30 1 to 2")
    donate = parse_command("!donate 40 1 в 9")

    assert attack.type == OrderType.ATTACK
    assert attack.units == 50
    assert attack.source_city_id == 1
    assert attack.target_city_id == 8
    assert move.type == OrderType.MOVE
    assert donate.type == OrderType.DONATE


def test_parse_upgrade_and_zombie_attack() -> None:
    upgrade = parse_command("!up 1")
    zattack = parse_command("!zattack 50 8")

    assert upgrade.type == OrderType.UPGRADE
    assert upgrade.city_id == 1
    assert zattack.type == OrderType.ZOMBIE_ATTACK
    assert zattack.units == 50
    assert zattack.target_city_id == 8


def test_button_id_roundtrip_and_stale_check() -> None:
    button = ButtonId(ButtonAction.LOCK_ORDERS, game_id=1, turn_number=2, team_id=3)

    parsed = parse_button_id(button.render())

    assert parsed == button
    ensure_fresh_button(parsed, current_turn=2)
    with pytest.raises(InvalidOrderError):
        ensure_fresh_button(parsed, current_turn=3)
