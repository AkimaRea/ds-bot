from __future__ import annotations

from datetime import datetime
from typing import Any

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


def game_to_dict(game: GameState) -> dict[str, Any]:
    return {
        "id": game.id,
        "guild_id": game.guild_id,
        "status": game.status.value,
        "current_turn": game.current_turn,
        "max_turns": game.max_turns,
        "processing_turn": game.processing_turn,
        "teams": [team_to_dict(team) for team in game.teams.values()],
        "cities": [city_to_dict(city) for city in game.cities.values()],
        "orders": [order_to_dict(order) for order in game.orders],
        "reservations": [reservation_to_dict(item) for item in game.reservations],
        "turn_history": [turn_history_to_dict(item) for item in game.turn_history],
        "admin_audit_log": [admin_audit_to_dict(item) for item in game.admin_audit_log],
    }


def game_from_dict(data: dict[str, Any]) -> GameState:
    return GameState(
        id=int(data["id"]),
        guild_id=data.get("guild_id"),
        status=GameStatus(data["status"]),
        current_turn=int(data["current_turn"]),
        max_turns=int(data["max_turns"]),
        processing_turn=bool(data.get("processing_turn", False)),
        teams={team.id: team for team in (team_from_dict(item) for item in data["teams"])},
        cities={city.id: city for city in (city_from_dict(item) for item in data["cities"])},
        orders=[order_from_dict(item) for item in data.get("orders", [])],
        reservations=[reservation_from_dict(item) for item in data.get("reservations", [])],
        turn_history=[turn_history_from_dict(item) for item in data.get("turn_history", [])],
        admin_audit_log=[
            admin_audit_from_dict(item) for item in data.get("admin_audit_log", [])
        ],
    )


def city_to_dict(city: City) -> dict[str, Any]:
    return {
        "id": city.id,
        "owner_type": city.owner_type.value,
        "owner_team_id": city.owner_team_id,
        "castle_level": city.castle_level,
        "units": city.units,
    }


def city_from_dict(data: dict[str, Any]) -> City:
    return City(
        id=int(data["id"]),
        owner_type=OwnerType(data["owner_type"]),
        owner_team_id=data.get("owner_team_id"),
        castle_level=int(data["castle_level"]),
        units=int(data["units"]),
    )


def team_to_dict(team: Team) -> dict[str, Any]:
    return {
        "id": team.id,
        "name": team.name,
        "color": team.color,
        "discord_role_id": team.discord_role_id,
        "discord_channel_id": team.discord_channel_id,
        "orders_locked": team.orders_locked,
        "donated_units_this_turn": team.donated_units_this_turn,
    }


def team_from_dict(data: dict[str, Any]) -> Team:
    return Team(
        id=int(data["id"]),
        name=str(data["name"]),
        color=str(data["color"]),
        discord_role_id=data.get("discord_role_id"),
        discord_channel_id=data.get("discord_channel_id"),
        orders_locked=bool(data["orders_locked"]),
        donated_units_this_turn=int(data["donated_units_this_turn"]),
    )


def order_to_dict(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "turn_number": order.turn_number,
        "actor_type": order.actor_type.value,
        "type": order.type.value,
        "units": order.units,
        "team_id": order.team_id,
        "source_city_id": order.source_city_id,
        "target_city_id": order.target_city_id,
        "upgrade_cost": order.upgrade_cost,
        "created_at": order.created_at.isoformat(),
    }


def order_from_dict(data: dict[str, Any]) -> Order:
    return Order(
        id=int(data["id"]),
        turn_number=int(data["turn_number"]),
        actor_type=OrderActorType(data["actor_type"]),
        type=OrderType(data["type"]),
        units=int(data["units"]),
        team_id=data.get("team_id"),
        source_city_id=data.get("source_city_id"),
        target_city_id=data.get("target_city_id"),
        upgrade_cost=data.get("upgrade_cost"),
        created_at=_datetime(data["created_at"]),
    )


def reservation_to_dict(reservation: UnitReservation) -> dict[str, Any]:
    return {
        "order_id": reservation.order_id,
        "turn_number": reservation.turn_number,
        "city_id": reservation.city_id,
        "units": reservation.units,
        "team_id": reservation.team_id,
    }


def reservation_from_dict(data: dict[str, Any]) -> UnitReservation:
    return UnitReservation(
        order_id=int(data["order_id"]),
        turn_number=int(data["turn_number"]),
        city_id=int(data["city_id"]),
        units=int(data["units"]),
        team_id=data.get("team_id"),
    )


def battle_to_dict(battle: BattleHistory) -> dict[str, Any]:
    return {
        "turn_number": battle.turn_number,
        "target_city_id": battle.target_city_id,
        "defender_owner_type": battle.defender_owner_type.value,
        "defender_team_id": battle.defender_team_id,
        "defender_units": battle.defender_units,
        "attackers": battle.attackers,
        "winner_owner_type": battle.winner_owner_type.value,
        "winner_team_id": battle.winner_team_id,
        "remaining_units": battle.remaining_units,
        "killed_units": battle.killed_units,
        "random_seed": battle.random_seed,
    }


def battle_from_dict(data: dict[str, Any]) -> BattleHistory:
    attackers = {
        _int_key_if_possible(key): value for key, value in data.get("attackers", {}).items()
    }
    return BattleHistory(
        turn_number=int(data["turn_number"]),
        target_city_id=int(data["target_city_id"]),
        defender_owner_type=OwnerType(data["defender_owner_type"]),
        defender_team_id=data.get("defender_team_id"),
        defender_units=int(data["defender_units"]),
        attackers=attackers,
        winner_owner_type=OwnerType(data["winner_owner_type"]),
        winner_team_id=data.get("winner_team_id"),
        remaining_units=int(data["remaining_units"]),
        killed_units=int(data["killed_units"]),
        random_seed=data.get("random_seed"),
    )


def turn_history_to_dict(history: TurnHistory) -> dict[str, Any]:
    return {
        "turn_number": history.turn_number,
        "killed_units": history.killed_units,
        "events": history.events,
        "battles": [battle_to_dict(battle) for battle in history.battles],
        "processed_at": history.processed_at.isoformat(),
    }


def turn_history_from_dict(data: dict[str, Any]) -> TurnHistory:
    return TurnHistory(
        turn_number=int(data["turn_number"]),
        killed_units=int(data["killed_units"]),
        events=list(data.get("events", [])),
        battles=[battle_from_dict(item) for item in data.get("battles", [])],
        processed_at=_datetime(data["processed_at"]),
    )


def admin_audit_to_dict(record: AdminAuditLog) -> dict[str, Any]:
    return {
        "turn_number": record.turn_number,
        "host_user_id": record.host_user_id,
        "action": record.action,
        "before": record.before,
        "after": record.after,
        "created_at": record.created_at.isoformat(),
    }


def admin_audit_from_dict(data: dict[str, Any]) -> AdminAuditLog:
    return AdminAuditLog(
        turn_number=int(data["turn_number"]),
        host_user_id=int(data["host_user_id"]),
        action=str(data["action"]),
        before=dict(data["before"]),
        after=dict(data["after"]),
        created_at=_datetime(data["created_at"]),
    )


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _int_key_if_possible(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value
