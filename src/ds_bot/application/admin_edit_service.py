from __future__ import annotations

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.enums import GameStatus, OwnerType
from ds_bot.domain.errors import InvalidOrderError
from ds_bot.domain.models import AdminAuditLog, GameState
from ds_bot.domain.rules import get_city, get_team


class AdminEditService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    def set_city_owner(
        self,
        city_id: int,
        owner_type: OwnerType,
        host_user_id: int,
        owner_team_id: int | None = None,
        guild_id: int | None = None,
    ) -> None:
        game = self._game(guild_id)
        city = get_city(game, city_id)
        if owner_type == OwnerType.TEAM:
            if owner_team_id is None:
                raise InvalidOrderError("Team owner requires owner_team_id.")
            get_team(game, owner_team_id)
        elif owner_team_id is not None:
            raise InvalidOrderError("Only team-owned cities may have owner_team_id.")

        before = _city_snapshot(city)
        city.owner_type = owner_type
        city.owner_team_id = owner_team_id
        self._audit(game, host_user_id, "set_city_owner", before, _city_snapshot(city))
        self.repository.save(game)

    def set_city_units(
        self,
        city_id: int,
        units: int,
        host_user_id: int,
        guild_id: int | None = None,
    ) -> None:
        if units < 0:
            raise InvalidOrderError("City units cannot be negative.")
        game = self._game(guild_id)
        city = get_city(game, city_id)
        before = _city_snapshot(city)
        city.units = units
        self._audit(game, host_user_id, "set_city_units", before, _city_snapshot(city))
        self.repository.save(game)

    def set_castle_level(
        self,
        city_id: int,
        castle_level: int,
        host_user_id: int,
        guild_id: int | None = None,
    ) -> None:
        if castle_level < 0 or castle_level > 3:
            raise InvalidOrderError("Castle level must be between 0 and 3.")
        game = self._game(guild_id)
        city = get_city(game, city_id)
        if city.owner_type != OwnerType.ZOMBIES and castle_level == 0:
            raise InvalidOrderError("Only the zombie city may have castle level 0.")
        before = _city_snapshot(city)
        city.castle_level = castle_level
        self._audit(game, host_user_id, "set_castle_level", before, _city_snapshot(city))
        self.repository.save(game)

    def set_current_turn(
        self,
        current_turn: int,
        host_user_id: int,
        guild_id: int | None = None,
    ) -> None:
        game = self._game(guild_id)
        if current_turn < 1 or current_turn > game.max_turns:
            raise InvalidOrderError("Current turn is out of range.")
        before = {"current_turn": game.current_turn}
        game.current_turn = current_turn
        self._audit(game, host_user_id, "set_current_turn", before, {"current_turn": current_turn})
        self.repository.save(game)

    def set_game_status(
        self,
        status: GameStatus,
        host_user_id: int,
        guild_id: int | None = None,
    ) -> None:
        game = self._game(guild_id)
        before = {"status": game.status.value}
        game.status = status
        self._audit(game, host_user_id, "set_game_status", before, {"status": status.value})
        self.repository.save(game)

    def _game(self, guild_id: int | None) -> GameState:
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Game was not created.")
        return game

    def _audit(
        self,
        game: GameState,
        host_user_id: int,
        action: str,
        before: dict[str, object],
        after: dict[str, object],
    ) -> None:
        game.admin_audit_log.append(
            AdminAuditLog(
                turn_number=game.current_turn,
                host_user_id=host_user_id,
                action=action,
                before=before,
                after=after,
            )
        )


def _city_snapshot(city) -> dict[str, object]:
    return {
        "city_id": city.id,
        "owner_type": city.owner_type.value,
        "owner_team_id": city.owner_team_id,
        "castle_level": city.castle_level,
        "units": city.units,
    }
