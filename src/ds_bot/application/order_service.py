from __future__ import annotations

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.models import GameState, Order
from ds_bot.domain.orders import (
    add_attack_order,
    add_donate_order,
    add_move_order,
    add_upgrade_order,
    add_zombie_attack_order,
    lock_team_orders,
)


class OrderService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    def add_attack(
        self,
        team_id: int,
        units: int,
        source_city_id: int,
        target_city_id: int,
        guild_id: int | None = None,
    ) -> Order:
        game = self._game(guild_id)
        order = add_attack_order(game, team_id, units, source_city_id, target_city_id)
        self.repository.save(game)
        return order

    def add_move(
        self,
        team_id: int,
        units: int,
        source_city_id: int,
        target_city_id: int,
        guild_id: int | None = None,
    ) -> Order:
        game = self._game(guild_id)
        order = add_move_order(game, team_id, units, source_city_id, target_city_id)
        self.repository.save(game)
        return order

    def add_donate(
        self,
        team_id: int,
        units: int,
        source_city_id: int,
        target_city_id: int,
        guild_id: int | None = None,
    ) -> Order:
        game = self._game(guild_id)
        order = add_donate_order(game, team_id, units, source_city_id, target_city_id)
        self.repository.save(game)
        return order

    def add_upgrade(self, team_id: int, city_id: int, guild_id: int | None = None) -> Order:
        game = self._game(guild_id)
        order = add_upgrade_order(game, team_id, city_id)
        self.repository.save(game)
        return order

    def add_zombie_attack(
        self,
        units: int,
        target_city_id: int,
        guild_id: int | None = None,
    ) -> Order:
        game = self._game(guild_id)
        order = add_zombie_attack_order(game, units, target_city_id)
        self.repository.save(game)
        return order

    def lock_orders(self, team_id: int, guild_id: int | None = None) -> None:
        game = self._game(guild_id)
        lock_team_orders(game, team_id)
        self.repository.save(game)

    def _game(self, guild_id: int | None) -> GameState:
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Игра не создана.")
        return game
