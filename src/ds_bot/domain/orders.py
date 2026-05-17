from __future__ import annotations

from ds_bot.domain.enums import OrderActorType, OrderType
from ds_bot.domain.errors import InvalidOrderError
from ds_bot.domain.initial_map import ZOMBIE_CITY_ID
from ds_bot.domain.models import GameState, Order, UnitReservation
from ds_bot.domain.rules import (
    ensure_available_units,
    ensure_game_active,
    ensure_orders_unlocked,
    ensure_positive_units,
    ensure_team_owns,
    get_city,
    get_team,
    team_total_units,
    upgrade_cost,
)


def add_attack_order(game: GameState, team_id: int, units: int, source_id: int, target_id: int) -> Order:
    _prepare_team_order(game, team_id, units)
    source = get_city(game, source_id)
    target = get_city(game, target_id)
    ensure_team_owns(source, team_id)
    ensure_available_units(game, source_id, units)
    if target_id == ZOMBIE_CITY_ID:
        raise InvalidOrderError("Город зомби нельзя атаковать.")
    if target.is_owned_by_team(team_id):
        raise InvalidOrderError("Нельзя атаковать свой город.")
    return _append_order(
        game,
        OrderType.ATTACK,
        units,
        team_id=team_id,
        source_city_id=source_id,
        target_city_id=target_id,
        reserve_city_id=source_id,
    )


def add_move_order(game: GameState, team_id: int, units: int, source_id: int, target_id: int) -> Order:
    _prepare_team_order(game, team_id, units)
    source = get_city(game, source_id)
    target = get_city(game, target_id)
    ensure_team_owns(source, team_id)
    ensure_team_owns(target, team_id)
    ensure_available_units(game, source_id, units)
    return _append_order(
        game,
        OrderType.MOVE,
        units,
        team_id=team_id,
        source_city_id=source_id,
        target_city_id=target_id,
        reserve_city_id=source_id,
    )


def add_donate_order(game: GameState, team_id: int, units: int, source_id: int, target_id: int) -> Order:
    _prepare_team_order(game, team_id, units)
    source = get_city(game, source_id)
    get_city(game, target_id)
    team = get_team(game, team_id)
    ensure_team_owns(source, team_id)
    ensure_available_units(game, source_id, units)
    if team.donated_units_this_turn + units > team_total_units(game, team_id):
        raise InvalidOrderError("Команда не может пожертвовать больше доступной армии.")
    team.donated_units_this_turn += units
    return _append_order(
        game,
        OrderType.DONATE,
        units,
        team_id=team_id,
        source_city_id=source_id,
        target_city_id=target_id,
        reserve_city_id=source_id,
    )


def add_upgrade_order(game: GameState, team_id: int, city_id: int) -> Order:
    ensure_game_active(game)
    ensure_orders_unlocked(game, team_id)
    city = get_city(game, city_id)
    ensure_team_owns(city, team_id)
    cost = upgrade_cost(city)
    ensure_available_units(game, city_id, cost)
    return _append_order(
        game,
        OrderType.UPGRADE,
        cost,
        team_id=team_id,
        source_city_id=city_id,
        target_city_id=city_id,
        upgrade_cost=cost,
        reserve_city_id=city_id,
    )


def add_zombie_attack_order(game: GameState, units: int, target_id: int) -> Order:
    ensure_game_active(game)
    ensure_positive_units(units)
    get_city(game, target_id)
    if target_id == ZOMBIE_CITY_ID:
        raise InvalidOrderError("Зомби не могут атаковать город зомби.")
    ensure_available_units(game, ZOMBIE_CITY_ID, units)
    return _append_order(
        game,
        OrderType.ZOMBIE_ATTACK,
        units,
        actor_type=OrderActorType.ZOMBIES,
        source_city_id=ZOMBIE_CITY_ID,
        target_city_id=target_id,
        reserve_city_id=ZOMBIE_CITY_ID,
    )


def lock_team_orders(game: GameState, team_id: int) -> None:
    ensure_game_active(game)
    get_team(game, team_id).orders_locked = True


def _prepare_team_order(game: GameState, team_id: int, units: int) -> None:
    ensure_game_active(game)
    ensure_orders_unlocked(game, team_id)
    ensure_positive_units(units)


def _append_order(
    game: GameState,
    order_type: OrderType,
    units: int,
    *,
    actor_type: OrderActorType = OrderActorType.TEAM,
    team_id: int | None = None,
    source_city_id: int | None = None,
    target_city_id: int | None = None,
    upgrade_cost: int | None = None,
    reserve_city_id: int | None = None,
) -> Order:
    order = Order(
        id=game.next_order_id(),
        turn_number=game.current_turn,
        actor_type=actor_type,
        team_id=team_id,
        type=order_type,
        source_city_id=source_city_id,
        target_city_id=target_city_id,
        units=units,
        upgrade_cost=upgrade_cost,
    )
    game.orders.append(order)
    if reserve_city_id is not None:
        game.reservations.append(
            UnitReservation(
                order_id=order.id,
                turn_number=game.current_turn,
                team_id=team_id,
                city_id=reserve_city_id,
                units=units,
            )
        )
    return order
