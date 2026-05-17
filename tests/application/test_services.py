from __future__ import annotations

from ds_bot.application.order_service import OrderService
from ds_bot.application.repositories import InMemoryGameRepository
from ds_bot.application.setup_service import SetupService
from ds_bot.application.status_service import StatusService
from ds_bot.application.turn_service import TurnService
from ds_bot.domain.enums import OwnerType


def test_application_services_run_first_game_flow() -> None:
    repository = InMemoryGameRepository()
    setup = SetupService(repository)
    orders = OrderService(repository)
    turns = TurnService(repository)
    statuses = StatusService(repository)

    setup.start_new_game(guild_id=42)
    orders.add_attack(team_id=1, units=80, source_city_id=1, target_city_id=5, guild_id=42)
    history = turns.end_turn(guild_id=42)

    game = repository.get_active_game(guild_id=42)
    assert game is not None
    assert game.cities[5].owner_type == OwnerType.BARBARIANS
    assert game.cities[5].units == 120
    assert history.killed_units == 160
    assert "Город #5" in statuses.host_status(guild_id=42)
    assert "Команда: Красный" in statuses.team_status(team_id=1, guild_id=42)
