from __future__ import annotations

from ds_bot.domain.engine import GameEngine
from ds_bot.domain.enums import GameStatus, OwnerType
from ds_bot.domain.initial_map import create_initial_game
from ds_bot.domain.orders import add_attack_order, add_donate_order, add_zombie_attack_order


def test_donation_is_applied_before_attack() -> None:
    game = create_initial_game()
    add_donate_order(game, team_id=1, units=40, source_id=1, target_id=5)
    add_attack_order(game, team_id=2, units=100, source_id=2, target_id=5)

    GameEngine().process_turn(game)

    assert game.cities[5].owner_type == OwnerType.BARBARIANS
    assert game.cities[5].units == 140


def test_multiple_team_attacks_choose_winner_by_largest_contribution() -> None:
    game = create_initial_game()
    add_attack_order(game, team_id=1, units=80, source_id=1, target_id=5)
    add_attack_order(game, team_id=2, units=60, source_id=2, target_id=5)

    history = GameEngine().process_turn(game)

    assert game.cities[5].owner_type == OwnerType.TEAM
    assert game.cities[5].owner_team_id == 1
    assert game.cities[5].units == 140
    assert history.battles[0].attackers == {1: 80, 2: 60}


def test_tied_attack_uses_seeded_random_winner() -> None:
    game = create_initial_game()
    game.cities[5].units = 50
    add_attack_order(game, team_id=1, units=80, source_id=1, target_id=5)
    add_attack_order(game, team_id=2, units=80, source_id=2, target_id=5)

    history = GameEngine(random_seed=7).process_turn(game)

    assert game.cities[5].owner_team_id in {1, 2}
    assert history.battles[0].random_seed == 7


def test_zombie_attack_does_not_change_target_owner_and_grows_from_kills() -> None:
    game = create_initial_game()
    game.cities[0].units = 50
    add_zombie_attack_order(game, units=50, target_id=5)

    history = GameEngine().process_turn(game)

    assert game.cities[5].owner_type == OwnerType.BARBARIANS
    assert game.cities[5].units == 150
    assert game.cities[0].units == 25
    assert history.killed_units == 50


def test_game_finishes_after_processing_sixth_turn() -> None:
    game = create_initial_game()
    engine = GameEngine()

    for _ in range(6):
        engine.process_turn(game)

    assert game.status == GameStatus.FINISHED
    assert game.current_turn == 6
