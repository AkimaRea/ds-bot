from __future__ import annotations

from ds_bot.domain.enums import GameStatus, OwnerType
from ds_bot.domain.models import City, GameState, Team


TEAM_SPECS: tuple[tuple[int, str, str, int], ...] = (
    (1, "Красный", "red", 1),
    (2, "Оранжевый", "orange", 2),
    (3, "Желтый", "yellow", 3),
    (4, "Зеленый", "green", 6),
    (5, "Бирюзовый", "cyan", 7),
    (6, "Синий", "blue", 11),
    (7, "Фиолетовый", "purple", 12),
    (8, "Розовый", "pink", 13),
)

BARBARIAN_CITY_IDS = (5, 9, 10, 15)
EMPTY_CITY_IDS = (4, 8, 14)
ZOMBIE_CITY_ID = 0


def create_initial_game(guild_id: int | None = None) -> GameState:
    teams: dict[int, Team] = {}
    cities: dict[int, City] = {
        ZOMBIE_CITY_ID: City(
            id=ZOMBIE_CITY_ID,
            owner_type=OwnerType.ZOMBIES,
            castle_level=0,
            units=0,
        )
    }

    for team_id, name, color, city_id in TEAM_SPECS:
        teams[team_id] = Team(id=team_id, name=name, color=color)
        cities[city_id] = City(
            id=city_id,
            owner_type=OwnerType.TEAM,
            owner_team_id=team_id,
            castle_level=1,
            units=100,
        )

    for city_id in BARBARIAN_CITY_IDS:
        cities[city_id] = City(
            id=city_id,
            owner_type=OwnerType.BARBARIANS,
            castle_level=1,
            units=100,
        )

    for city_id in EMPTY_CITY_IDS:
        cities[city_id] = City(
            id=city_id,
            owner_type=OwnerType.EMPTY,
            owner_team_id=None,
            castle_level=1,
            units=0,
        )

    return GameState(
        guild_id=guild_id,
        status=GameStatus.ACTIVE,
        current_turn=1,
        max_turns=6,
        teams=teams,
        cities=dict(sorted(cities.items())),
    )
