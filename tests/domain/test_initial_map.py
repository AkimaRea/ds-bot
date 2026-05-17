from __future__ import annotations

from ds_bot.domain.enums import GameStatus, OwnerType
from ds_bot.domain.initial_map import create_initial_game


def test_initial_map_matches_spec() -> None:
    game = create_initial_game()

    assert game.status == GameStatus.ACTIVE
    assert game.current_turn == 1
    assert game.max_turns == 6
    assert len(game.teams) == 8
    assert set(game.cities) == set(range(16))

    assert game.cities[0].owner_type == OwnerType.ZOMBIES
    assert game.cities[0].units == 0

    assert game.cities[1].owner_team_id == 1
    assert game.cities[13].owner_team_id == 8
    for city_id in (1, 2, 3, 6, 7, 11, 12, 13):
        assert game.cities[city_id].owner_type == OwnerType.TEAM
        assert game.cities[city_id].castle_level == 1
        assert game.cities[city_id].units == 100

    for city_id in (5, 9, 10, 15):
        assert game.cities[city_id].owner_type == OwnerType.BARBARIANS
        assert game.cities[city_id].units == 100

    for city_id in (4, 8, 14):
        assert game.cities[city_id].owner_type == OwnerType.EMPTY
        assert game.cities[city_id].units == 0
