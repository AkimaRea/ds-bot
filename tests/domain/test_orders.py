from __future__ import annotations

import pytest

from ds_bot.domain.errors import InsufficientUnitsError, OrdersLockedError
from ds_bot.domain.initial_map import create_initial_game
from ds_bot.domain.orders import add_attack_order, add_move_order, lock_team_orders
from ds_bot.domain.rules import available_units


def test_reservation_prevents_spending_more_than_available_units() -> None:
    game = create_initial_game()

    add_attack_order(game, team_id=1, units=80, source_id=1, target_id=5)

    assert available_units(game, 1) == 20
    with pytest.raises(InsufficientUnitsError):
        add_move_order(game, team_id=1, units=30, source_id=1, target_id=1)


def test_locked_orders_reject_new_team_orders() -> None:
    game = create_initial_game()

    lock_team_orders(game, team_id=1)

    with pytest.raises(OrdersLockedError):
        add_attack_order(game, team_id=1, units=10, source_id=1, target_id=5)
