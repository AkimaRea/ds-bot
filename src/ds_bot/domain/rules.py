from __future__ import annotations

from ds_bot.domain.enums import GameStatus, OwnerType
from ds_bot.domain.errors import (
    CityNotFoundError,
    GameNotActiveError,
    InsufficientUnitsError,
    InvalidOrderError,
    OrdersLockedError,
    OwnershipError,
    TeamNotFoundError,
)
from ds_bot.domain.models import City, GameState, Team

UPGRADE_COSTS = {1: 200, 2: 300}
MAX_CASTLE_LEVEL = 3


def ensure_game_active(game: GameState) -> None:
    if game.status != GameStatus.ACTIVE:
        raise GameNotActiveError("Игра не активна.")


def get_city(game: GameState, city_id: int) -> City:
    try:
        return game.cities[city_id]
    except KeyError as exc:
        raise CityNotFoundError(f"Город #{city_id} не существует.") from exc


def get_team(game: GameState, team_id: int) -> Team:
    try:
        return game.teams[team_id]
    except KeyError as exc:
        raise TeamNotFoundError(f"Команда #{team_id} не существует.") from exc


def ensure_orders_unlocked(game: GameState, team_id: int) -> None:
    team = get_team(game, team_id)
    if team.orders_locked:
        raise OrdersLockedError("Приказ команды уже отправлен.")


def ensure_positive_units(units: int) -> None:
    if units <= 0:
        raise InvalidOrderError("Количество юнитов должно быть положительным.")


def ensure_team_owns(city: City, team_id: int) -> None:
    if not city.is_owned_by_team(team_id):
        raise OwnershipError(f"Город #{city.id} не принадлежит команде.")


def reserved_units(game: GameState, city_id: int) -> int:
    return sum(
        reservation.units
        for reservation in game.reservations_for_current_turn()
        if reservation.city_id == city_id
    )


def available_units(game: GameState, city_id: int) -> int:
    city = get_city(game, city_id)
    return city.units - reserved_units(game, city_id)


def ensure_available_units(game: GameState, city_id: int, units: int) -> None:
    free_units = available_units(game, city_id)
    if free_units < units:
        raise InsufficientUnitsError(
            f"В городе #{city_id} доступно {free_units} юнитов, требуется {units}."
        )


def team_total_units(game: GameState, team_id: int) -> int:
    return sum(city.units for city in game.cities.values() if city.is_owned_by_team(team_id))


def castle_income(city: City) -> int:
    if city.owner_type == OwnerType.EMPTY or city.owner_type == OwnerType.ZOMBIES:
        return 0
    if city.owner_type == OwnerType.BARBARIANS:
        return 100
    return city.castle_level * 100


def upgrade_cost(city: City) -> int:
    try:
        return UPGRADE_COSTS[city.castle_level]
    except KeyError as exc:
        raise InvalidOrderError("Город уже имеет максимальный уровень замка.") from exc
