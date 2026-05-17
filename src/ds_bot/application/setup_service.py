from __future__ import annotations

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.initial_map import create_initial_game
from ds_bot.domain.models import GameState


class SetupService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    def start_new_game(self, guild_id: int | None = None) -> GameState:
        game = create_initial_game(guild_id=guild_id)
        self.repository.save(game)
        return game
