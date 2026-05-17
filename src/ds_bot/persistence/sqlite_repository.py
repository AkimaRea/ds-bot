from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.enums import GameStatus, OrderActorType, OrderType, OwnerType
from ds_bot.domain.models import (
    AdminAuditLog,
    BattleHistory,
    City,
    GameState,
    Order,
    Team,
    TurnHistory,
    UnitReservation,
)
from ds_bot.persistence.db import connect_sqlite, initialize_database


class SQLiteGameRepository(GameRepository):
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        with self._connect() as connection:
            initialize_database(connection)

    def get_active_game(self, guild_id: int | None = None) -> GameState | None:
        with self._connect() as connection:
            if guild_id is None:
                row = connection.execute(
                    "SELECT * FROM games ORDER BY id DESC LIMIT 1"
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM games WHERE guild_id = ? ORDER BY id DESC LIMIT 1",
                    (guild_id,),
                ).fetchone()
            if row is None:
                return None
            return self._load_game(connection, int(row["id"]))

    def save(self, game: GameState) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN")
            self._replace_game(connection, game)
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.database_path)

    def _replace_game(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.execute("DELETE FROM games WHERE id = ?", (game.id,))
        connection.execute(
            """
            INSERT INTO games (id, guild_id, status, current_turn, max_turns, processing_turn)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                game.id,
                game.guild_id,
                game.status.value,
                game.current_turn,
                game.max_turns,
                int(game.processing_turn),
            ),
        )
        self._insert_teams(connection, game)
        self._insert_cities(connection, game)
        self._insert_orders(connection, game)
        self._insert_reservations(connection, game)
        self._insert_history(connection, game)
        self._insert_admin_audit(connection, game)

    def _insert_teams(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.executemany(
            """
            INSERT INTO teams (
              id, game_id, name, color, discord_role_id, discord_channel_id,
              orders_locked, donated_units_this_turn
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    team.id,
                    game.id,
                    team.name,
                    team.color,
                    team.discord_role_id,
                    team.discord_channel_id,
                    int(team.orders_locked),
                    team.donated_units_this_turn,
                )
                for team in game.teams.values()
            ],
        )

    def _insert_cities(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.executemany(
            """
            INSERT INTO cities (id, game_id, owner_type, owner_team_id, castle_level, units)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    city.id,
                    game.id,
                    city.owner_type.value,
                    city.owner_team_id,
                    city.castle_level,
                    city.units,
                )
                for city in game.cities.values()
            ],
        )

    def _insert_orders(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.executemany(
            """
            INSERT INTO orders (
              id, game_id, turn_number, actor_type, team_id, type,
              source_city_id, target_city_id, units, upgrade_cost, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    order.id,
                    game.id,
                    order.turn_number,
                    order.actor_type.value,
                    order.team_id,
                    order.type.value,
                    order.source_city_id,
                    order.target_city_id,
                    order.units,
                    order.upgrade_cost,
                    order.created_at.isoformat(),
                )
                for order in game.orders
            ],
        )

    def _insert_reservations(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.executemany(
            """
            INSERT INTO unit_reservations (
              game_id, turn_number, team_id, city_id, order_id, units
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    game.id,
                    reservation.turn_number,
                    reservation.team_id,
                    reservation.city_id,
                    reservation.order_id,
                    reservation.units,
                )
                for reservation in game.reservations
            ],
        )

    def _insert_history(self, connection: sqlite3.Connection, game: GameState) -> None:
        for history in game.turn_history:
            connection.execute(
                """
                INSERT INTO turn_history (
                  game_id, turn_number, killed_units, events_json, processed_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    game.id,
                    history.turn_number,
                    history.killed_units,
                    json.dumps(history.events, ensure_ascii=False),
                    history.processed_at.isoformat(),
                ),
            )
            connection.executemany(
                """
                INSERT INTO battle_history (
                  game_id, turn_number, target_city_id, defender_owner_type,
                  defender_team_id, defender_units, attackers_json, winner_owner_type,
                  winner_team_id, remaining_units, killed_units, random_seed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        game.id,
                        battle.turn_number,
                        battle.target_city_id,
                        battle.defender_owner_type.value,
                        battle.defender_team_id,
                        battle.defender_units,
                        json.dumps(battle.attackers, ensure_ascii=False),
                        battle.winner_owner_type.value,
                        battle.winner_team_id,
                        battle.remaining_units,
                        battle.killed_units,
                        battle.random_seed,
                    )
                    for battle in history.battles
                ],
            )

    def _insert_admin_audit(self, connection: sqlite3.Connection, game: GameState) -> None:
        connection.executemany(
            """
            INSERT INTO admin_audit_log (
              game_id, turn_number, host_user_id, action, before_json, after_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    game.id,
                    record.turn_number,
                    record.host_user_id,
                    record.action,
                    json.dumps(record.before, ensure_ascii=False),
                    json.dumps(record.after, ensure_ascii=False),
                    record.created_at.isoformat(),
                )
                for record in game.admin_audit_log
            ],
        )

    def _load_game(self, connection: sqlite3.Connection, game_id: int) -> GameState:
        game_row = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if game_row is None:
            raise RuntimeError(f"Game {game_id} was not found.")

        teams = {
            int(row["id"]): Team(
                id=int(row["id"]),
                name=str(row["name"]),
                color=str(row["color"]),
                discord_role_id=row["discord_role_id"],
                discord_channel_id=row["discord_channel_id"],
                orders_locked=bool(row["orders_locked"]),
                donated_units_this_turn=int(row["donated_units_this_turn"]),
            )
            for row in connection.execute("SELECT * FROM teams WHERE game_id = ?", (game_id,))
        }
        cities = {
            int(row["id"]): City(
                id=int(row["id"]),
                owner_type=OwnerType(row["owner_type"]),
                owner_team_id=row["owner_team_id"],
                castle_level=int(row["castle_level"]),
                units=int(row["units"]),
            )
            for row in connection.execute("SELECT * FROM cities WHERE game_id = ?", (game_id,))
        }
        orders = [
            Order(
                id=int(row["id"]),
                turn_number=int(row["turn_number"]),
                actor_type=OrderActorType(row["actor_type"]),
                team_id=row["team_id"],
                type=OrderType(row["type"]),
                source_city_id=row["source_city_id"],
                target_city_id=row["target_city_id"],
                units=int(row["units"]),
                upgrade_cost=row["upgrade_cost"],
            )
            for row in connection.execute("SELECT * FROM orders WHERE game_id = ?", (game_id,))
        ]
        reservations = [
            UnitReservation(
                order_id=int(row["order_id"]),
                turn_number=int(row["turn_number"]),
                city_id=int(row["city_id"]),
                units=int(row["units"]),
                team_id=row["team_id"],
            )
            for row in connection.execute(
                "SELECT * FROM unit_reservations WHERE game_id = ?", (game_id,)
            )
        ]

        battles_by_turn = self._load_battles_by_turn(connection, game_id)
        turn_history = [
            TurnHistory(
                turn_number=int(row["turn_number"]),
                killed_units=int(row["killed_units"]),
                events=json.loads(row["events_json"]),
                battles=battles_by_turn.get(int(row["turn_number"]), []),
            )
            for row in connection.execute(
                "SELECT * FROM turn_history WHERE game_id = ? ORDER BY turn_number",
                (game_id,),
            )
        ]
        admin_audit_log = [
            AdminAuditLog(
                turn_number=int(row["turn_number"]),
                host_user_id=int(row["host_user_id"]),
                action=str(row["action"]),
                before=json.loads(row["before_json"]),
                after=json.loads(row["after_json"]),
            )
            for row in connection.execute(
                "SELECT * FROM admin_audit_log WHERE game_id = ? ORDER BY id",
                (game_id,),
            )
        ]
        return GameState(
            id=int(game_row["id"]),
            guild_id=game_row["guild_id"],
            status=GameStatus(game_row["status"]),
            current_turn=int(game_row["current_turn"]),
            max_turns=int(game_row["max_turns"]),
            processing_turn=bool(game_row["processing_turn"]),
            teams=teams,
            cities=cities,
            orders=orders,
            reservations=reservations,
            turn_history=turn_history,
            admin_audit_log=admin_audit_log,
        )

    def _load_battles_by_turn(
        self,
        connection: sqlite3.Connection,
        game_id: int,
    ) -> dict[int, list[BattleHistory]]:
        battles_by_turn: dict[int, list[BattleHistory]] = {}
        for row in connection.execute(
            "SELECT * FROM battle_history WHERE game_id = ? ORDER BY id",
            (game_id,),
        ):
            turn_number = int(row["turn_number"])
            attackers = {
                _int_key_if_possible(key): int(value)
                for key, value in json.loads(row["attackers_json"]).items()
            }
            battles_by_turn.setdefault(turn_number, []).append(
                BattleHistory(
                    turn_number=turn_number,
                    target_city_id=int(row["target_city_id"]),
                    defender_owner_type=OwnerType(row["defender_owner_type"]),
                    defender_team_id=row["defender_team_id"],
                    defender_units=int(row["defender_units"]),
                    attackers=attackers,
                    winner_owner_type=OwnerType(row["winner_owner_type"]),
                    winner_team_id=row["winner_team_id"],
                    remaining_units=int(row["remaining_units"]),
                    killed_units=int(row["killed_units"]),
                    random_seed=row["random_seed"],
                )
            )
        return battles_by_turn


def _int_key_if_possible(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value
