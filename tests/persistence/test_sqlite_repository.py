from __future__ import annotations

from ds_bot.application.order_service import OrderService
from ds_bot.application.setup_service import SetupService
from ds_bot.application.turn_service import TurnService
from ds_bot.domain.enums import OwnerType
from ds_bot.persistence.sqlite_repository import SQLiteGameRepository


def test_sqlite_repository_persists_game_state(tmp_path) -> None:
    repository = SQLiteGameRepository(tmp_path / "game.sqlite3")
    setup = SetupService(repository)
    orders = OrderService(repository)
    turns = TurnService(repository)

    setup.start_new_game(guild_id=100)
    orders.add_attack(team_id=1, units=80, source_city_id=1, target_city_id=5, guild_id=100)
    turns.end_turn(guild_id=100)

    reloaded_repository = SQLiteGameRepository(tmp_path / "game.sqlite3")
    game = reloaded_repository.get_active_game(guild_id=100)

    assert game is not None
    assert game.current_turn == 2
    assert game.cities[5].owner_type == OwnerType.BARBARIANS
    assert game.cities[5].units == 120
    assert len(game.turn_history) == 1
    assert game.turn_history[0].killed_units == 160
