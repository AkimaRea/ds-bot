from __future__ import annotations

from typing import Protocol

from ds_bot.domain.models import GameState


class GameRepository(Protocol):
    def get_active_game(self, guild_id: int | None = None) -> GameState | None:
        raise NotImplementedError

    def save(self, game: GameState) -> None:
        raise NotImplementedError


class InMemoryGameRepository:
    def __init__(self) -> None:
        self.game: GameState | None = None

    def get_active_game(self, guild_id: int | None = None) -> GameState | None:
        if self.game is None:
            return None
        if guild_id is not None and self.game.guild_id != guild_id:
            return None
        return self.game

    def save(self, game: GameState) -> None:
        self.game = game
