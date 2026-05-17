from __future__ import annotations

from ds_bot.domain.enums import OwnerType
from ds_bot.domain.models import City, GameState
from ds_bot.domain.rules import get_team


def render_host_status(game: GameState) -> str:
    lines = [f"Ход: {game.current_turn} / {game.max_turns}", ""]
    for city in sorted(game.cities.values(), key=lambda item: item.id):
        lines.append(_render_city_for_host(game, city))
    return "\n".join(lines)


def render_team_status(game: GameState, team_id: int) -> str:
    team = get_team(game, team_id)
    lock_status = "отправлен" if team.orders_locked else "не отправлен"
    lines = [
        f"Ход: {game.current_turn} / {game.max_turns}",
        f"Команда: {team.name}",
        f"Приказ: {lock_status}",
        "",
        "Ваши города:",
    ]
    team_cities = [
        city for city in sorted(game.cities.values(), key=lambda item: item.id)
        if city.is_owned_by_team(team_id)
    ]
    if not team_cities:
        lines.append("Нет городов.")
    for city in team_cities:
        lines.append(f"Город #{city.id} | Уровень: {city.castle_level} | Юниты: {city.units}")
    return "\n".join(lines)


def render_zombie_status(game: GameState) -> str:
    return f"Зомби | Юниты: {game.cities[0].units}"


def _render_city_for_host(game: GameState, city: City) -> str:
    owner = _owner_name(game, city)
    if city.owner_type == OwnerType.ZOMBIES:
        return f"Город #{city.id} | {owner} | Юниты: {city.units}"
    return (
        f"Город #{city.id} | {owner} | "
        f"Уровень: {city.castle_level} | Юниты: {city.units}"
    )


def _owner_name(game: GameState, city: City) -> str:
    if city.owner_type == OwnerType.TEAM and city.owner_team_id is not None:
        return game.teams[city.owner_team_id].name
    if city.owner_type == OwnerType.BARBARIANS:
        return "Варвары"
    if city.owner_type == OwnerType.ZOMBIES:
        return "Зомби"
    return "Пустой"
