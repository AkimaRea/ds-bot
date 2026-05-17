from __future__ import annotations

import random
from collections import defaultdict

from ds_bot.domain.enums import GameStatus, OrderType, OwnerType, TurnPhase
from ds_bot.domain.errors import DomainError, InvalidOrderError
from ds_bot.domain.initial_map import ZOMBIE_CITY_ID
from ds_bot.domain.models import BattleHistory, City, GameState, Order, TurnHistory
from ds_bot.domain.rules import castle_income, ensure_game_active, get_city


class GameEngine:
    def __init__(self, random_seed: int | None = None) -> None:
        self.random_seed = random_seed

    def process_turn(self, game: GameState) -> TurnHistory:
        ensure_game_active(game)
        if game.processing_turn:
            raise DomainError("Ход уже обрабатывается.")
        if any(history.turn_number == game.current_turn for history in game.turn_history):
            raise DomainError("Этот ход уже был обработан.")

        game.processing_turn = True
        events: list[str] = []
        battles: list[BattleHistory] = []
        killed_units = 0

        try:
            orders = game.orders_for_current_turn()
            self._process_moves(game, _orders_of_type(orders, OrderType.MOVE), events)
            self._process_donations(game, _orders_of_type(orders, OrderType.DONATE), events)
            self._process_upgrades(game, _orders_of_type(orders, OrderType.UPGRADE), events)
            killed_units += self._process_attacks(
                game,
                _orders_of_type(orders, OrderType.ATTACK),
                events,
                battles,
            )
            killed_units += self._process_zombie_attacks(
                game,
                _orders_of_type(orders, OrderType.ZOMBIE_ATTACK),
                events,
                battles,
            )
            self._process_income(game, events)
            self._process_zombie_growth(game, killed_units, events)

            history = TurnHistory(
                turn_number=game.current_turn,
                killed_units=killed_units,
                events=events,
                battles=battles,
            )
            game.turn_history.append(history)
            self._finish_turn(game)
            return history
        finally:
            game.processing_turn = False

    def _process_moves(self, game: GameState, orders: list[Order], events: list[str]) -> None:
        for order in orders:
            source, target = _source_and_target(game, order)
            source.units -= order.units
            target.units += order.units
            events.append(
                f"{TurnPhase.MOVEMENT}: {order.units} юнитов из #{source.id} в #{target.id}."
            )

    def _process_donations(self, game: GameState, orders: list[Order], events: list[str]) -> None:
        for order in orders:
            source, target = _source_and_target(game, order)
            source.units -= order.units
            target.units += order.units
            events.append(
                f"{TurnPhase.DONATION}: {order.units} юнитов из #{source.id} в #{target.id}."
            )

    def _process_upgrades(self, game: GameState, orders: list[Order], events: list[str]) -> None:
        for order in orders:
            if order.source_city_id is None or order.upgrade_cost is None:
                raise InvalidOrderError("Некорректный приказ улучшения.")
            city = get_city(game, order.source_city_id)
            city.units -= order.upgrade_cost
            city.castle_level += 1
            events.append(
                f"{TurnPhase.UPGRADE}: город #{city.id} улучшен до уровня {city.castle_level}."
            )

    def _process_attacks(
        self,
        game: GameState,
        orders: list[Order],
        events: list[str],
        battles: list[BattleHistory],
    ) -> int:
        killed_units = 0
        for target_id, target_orders in _group_by_target(orders).items():
            target = get_city(game, target_id)
            defender_owner_type = target.owner_type
            defender_team_id = target.owner_team_id
            defender_units = target.units
            contributions: dict[int, int] = defaultdict(int)

            for order in target_orders:
                if order.team_id is None or order.source_city_id is None:
                    raise InvalidOrderError("Некорректный приказ атаки.")
                source = get_city(game, order.source_city_id)
                source.units -= order.units
                contributions[order.team_id] += order.units

            total_attack = sum(contributions.values())
            if total_attack > defender_units:
                winner_team_id = self._choose_winner(contributions)
                remaining = total_attack - defender_units
                target.owner_type = OwnerType.TEAM
                target.owner_team_id = winner_team_id
                target.units = remaining
            else:
                winner_team_id = defender_team_id
                remaining = defender_units - total_attack
                target.units = remaining

            battle_kills = _battle_kills(total_attack, defender_units)
            killed_units += battle_kills
            battle = BattleHistory(
                turn_number=game.current_turn,
                target_city_id=target_id,
                defender_owner_type=defender_owner_type,
                defender_team_id=defender_team_id,
                defender_units=defender_units,
                attackers=dict(contributions),
                winner_owner_type=target.owner_type,
                winner_team_id=target.owner_team_id,
                remaining_units=target.units,
                killed_units=battle_kills,
                random_seed=self.random_seed,
            )
            battles.append(battle)
            events.append(
                f"{TurnPhase.ATTACK}: город #{target_id}, атака {total_attack}, "
                f"защита {defender_units}, остаток {target.units}."
            )
        return killed_units

    def _process_zombie_attacks(
        self,
        game: GameState,
        orders: list[Order],
        events: list[str],
        battles: list[BattleHistory],
    ) -> int:
        killed_units = 0
        zombie_city = get_city(game, ZOMBIE_CITY_ID)
        for order in orders:
            if order.target_city_id is None:
                raise InvalidOrderError("Некорректный приказ атаки зомби.")
            target = get_city(game, order.target_city_id)
            defender_units = target.units
            defender_owner_type = target.owner_type
            defender_team_id = target.owner_team_id

            zombie_city.units -= order.units
            target.units = max(defender_units - order.units, 0)
            battle_kills = min(order.units, defender_units)
            killed_units += battle_kills
            battles.append(
                BattleHistory(
                    turn_number=game.current_turn,
                    target_city_id=target.id,
                    defender_owner_type=defender_owner_type,
                    defender_team_id=defender_team_id,
                    defender_units=defender_units,
                    attackers={"zombies": order.units},
                    winner_owner_type=target.owner_type,
                    winner_team_id=target.owner_team_id,
                    remaining_units=target.units,
                    killed_units=battle_kills,
                    random_seed=None,
                )
            )
            events.append(
                f"{TurnPhase.ZOMBIE_ATTACK}: зомби атаковали #{target.id} на {order.units}."
            )
        return killed_units

    def _process_income(self, game: GameState, events: list[str]) -> None:
        for city in game.cities.values():
            income = castle_income(city)
            if income:
                city.units += income
                events.append(f"{TurnPhase.INCOME}: город #{city.id} получил {income}.")

    def _process_zombie_growth(
        self,
        game: GameState,
        killed_units: int,
        events: list[str],
    ) -> None:
        growth = killed_units // 2
        if growth:
            game.cities[ZOMBIE_CITY_ID].units += growth
        events.append(f"{TurnPhase.ZOMBIE_GROWTH}: зомби получили {growth}.")

    def _choose_winner(self, contributions: dict[int, int]) -> int:
        max_contribution = max(contributions.values())
        candidates = [
            team_id
            for team_id, contribution in contributions.items()
            if contribution == max_contribution
        ]
        if len(candidates) == 1:
            return candidates[0]
        rng = random.Random(self.random_seed)
        return rng.choice(sorted(candidates))

    def _finish_turn(self, game: GameState) -> None:
        game.orders.clear()
        game.reservations.clear()
        for team in game.teams.values():
            team.orders_locked = False
            team.donated_units_this_turn = 0

        if game.current_turn >= game.max_turns:
            game.status = GameStatus.FINISHED
        else:
            game.current_turn += 1


def _orders_of_type(orders: list[Order], order_type: OrderType) -> list[Order]:
    return [order for order in orders if order.type == order_type]


def _group_by_target(orders: list[Order]) -> dict[int, list[Order]]:
    grouped: dict[int, list[Order]] = defaultdict(list)
    for order in orders:
        if order.target_city_id is None:
            raise InvalidOrderError("Приказ без города назначения.")
        grouped[order.target_city_id].append(order)
    return grouped


def _source_and_target(game: GameState, order: Order) -> tuple[City, City]:
    if order.source_city_id is None or order.target_city_id is None:
        raise InvalidOrderError("Приказ без города источника или назначения.")
    return get_city(game, order.source_city_id), get_city(game, order.target_city_id)


def _battle_kills(total_attack: int, defender_units: int) -> int:
    return min(total_attack, defender_units) * 2
