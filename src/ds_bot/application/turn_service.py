from __future__ import annotations

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.engine import GameEngine
from ds_bot.domain.models import TurnHistory


class TurnService:
    def __init__(self, repository: GameRepository, engine: GameEngine | None = None) -> None:
        self.repository = repository
        self.engine = engine or GameEngine()

    def end_turn(self, guild_id: int | None = None) -> TurnHistory:
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Игра не создана.")
        history = self.engine.process_turn(game)
        self.repository.save(game)
        return history
