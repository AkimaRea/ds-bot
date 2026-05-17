from __future__ import annotations

from ds_bot.domain.models import GameState
from ds_bot.domain.status import render_host_status, render_team_status, render_zombie_status


def host_status_message(game: GameState) -> str:
    return render_host_status(game)


def team_status_message(game: GameState, team_id: int) -> str:
    return render_team_status(game, team_id)


def zombie_status_message(game: GameState) -> str:
    return render_zombie_status(game)
