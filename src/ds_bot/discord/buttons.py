from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ds_bot.domain.errors import InvalidOrderError


class ButtonAction(StrEnum):
    START_GAME = "start_game"
    END_TURN = "end_turn"
    LOCK_ORDERS = "lock_orders"


@dataclass(frozen=True, slots=True)
class ButtonId:
    action: ButtonAction
    game_id: int
    turn_number: int
    team_id: int | None = None

    def render(self) -> str:
        parts = ["dsbot", self.action.value, str(self.game_id), str(self.turn_number)]
        if self.team_id is not None:
            parts.append(str(self.team_id))
        return ":".join(parts)


def parse_button_id(custom_id: str) -> ButtonId:
    parts = custom_id.split(":")
    if len(parts) not in (4, 5) or parts[0] != "dsbot":
        raise InvalidOrderError("Unknown button id.")
    try:
        team_id = int(parts[4]) if len(parts) == 5 else None
        return ButtonId(
            action=ButtonAction(parts[1]),
            game_id=int(parts[2]),
            turn_number=int(parts[3]),
            team_id=team_id,
        )
    except ValueError as exc:
        raise InvalidOrderError("Invalid button id.") from exc


def ensure_fresh_button(button: ButtonId, current_turn: int) -> None:
    if button.turn_number != current_turn:
        raise InvalidOrderError("Button belongs to another turn.")
