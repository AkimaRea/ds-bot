from __future__ import annotations

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.status import render_host_status, render_team_status, render_zombie_status


class StatusService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    def host_status(self, guild_id: int | None = None) -> str:
        game = self._game(guild_id)
        return render_host_status(game)

    def team_status(self, team_id: int, guild_id: int | None = None) -> str:
        game = self._game(guild_id)
        return render_team_status(game, team_id)

    def zombie_status(self, guild_id: int | None = None) -> str:
        game = self._game(guild_id)
        return render_zombie_status(game)

    def _game(self, guild_id: int | None):
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Игра не создана.")
        return game
