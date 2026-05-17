from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC

from ds_bot.domain.enums import GameStatus, OrderActorType, OrderType, OwnerType


@dataclass(slots=True)
class City:
    id: int
    owner_type: OwnerType
    owner_team_id: int | None = None
    castle_level: int = 1
    units: int = 0

    def is_owned_by_team(self, team_id: int) -> bool:
        return self.owner_type == OwnerType.TEAM and self.owner_team_id == team_id


@dataclass(slots=True)
class Team:
    id: int
    name: str
    color: str
    discord_role_id: int | None = None
    discord_channel_id: int | None = None
    orders_locked: bool = False
    donated_units_this_turn: int = 0


@dataclass(slots=True)
class Order:
    id: int
    turn_number: int
    actor_type: OrderActorType
    type: OrderType
    units: int
    team_id: int | None = None
    source_city_id: int | None = None
    target_city_id: int | None = None
    upgrade_cost: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class UnitReservation:
    order_id: int
    turn_number: int
    city_id: int
    units: int
    team_id: int | None = None


@dataclass(slots=True)
class BattleHistory:
    turn_number: int
    target_city_id: int
    defender_owner_type: OwnerType
    defender_team_id: int | None
    defender_units: int
    attackers: dict[int | str, int]
    winner_owner_type: OwnerType
    winner_team_id: int | None
    remaining_units: int
    killed_units: int
    random_seed: int | None = None


@dataclass(slots=True)
class TurnHistory:
    turn_number: int
    killed_units: int
    events: list[str]
    battles: list[BattleHistory]
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class GameState:
    id: int = 1
    guild_id: int | None = None
    status: GameStatus = GameStatus.NOT_STARTED
    current_turn: int = 1
    max_turns: int = 6
    processing_turn: bool = False
    teams: dict[int, Team] = field(default_factory=dict)
    cities: dict[int, City] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    reservations: list[UnitReservation] = field(default_factory=list)
    turn_history: list[TurnHistory] = field(default_factory=list)

    def next_order_id(self) -> int:
        if not self.orders:
            return 1
        return max(order.id for order in self.orders) + 1

    def orders_for_current_turn(self) -> list[Order]:
        return [order for order in self.orders if order.turn_number == self.current_turn]

    def reservations_for_current_turn(self) -> list[UnitReservation]:
        return [
            reservation
            for reservation in self.reservations
            if reservation.turn_number == self.current_turn
        ]
