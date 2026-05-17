from __future__ import annotations

import re
from dataclasses import dataclass

from ds_bot.domain.enums import OrderType
from ds_bot.domain.errors import InvalidOrderError

_TEAM_ORDER_RE = re.compile(
    r"^!(?P<command>attack|move|donate)\s+"
    r"(?P<units>\d+)\s+"
    r"(?P<source>\d+)\s+"
    r"(?:в|to)\s+"
    r"(?P<target>\d+)\s*$",
    re.IGNORECASE,
)
_UPGRADE_RE = re.compile(r"^!up\s+(?P<city>\d+)\s*$", re.IGNORECASE)
_ZOMBIE_ATTACK_RE = re.compile(
    r"^!zattack\s+(?P<units>\d+)\s+(?P<target>\d+)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    type: OrderType
    units: int | None = None
    source_city_id: int | None = None
    target_city_id: int | None = None
    city_id: int | None = None


def parse_command(content: str) -> ParsedCommand:
    text = content.strip()
    if match := _TEAM_ORDER_RE.match(text):
        order_type = {
            "attack": OrderType.ATTACK,
            "move": OrderType.MOVE,
            "donate": OrderType.DONATE,
        }[match.group("command").lower()]
        return ParsedCommand(
            type=order_type,
            units=int(match.group("units")),
            source_city_id=int(match.group("source")),
            target_city_id=int(match.group("target")),
        )
    if match := _UPGRADE_RE.match(text):
        return ParsedCommand(type=OrderType.UPGRADE, city_id=int(match.group("city")))
    if match := _ZOMBIE_ATTACK_RE.match(text):
        return ParsedCommand(
            type=OrderType.ZOMBIE_ATTACK,
            units=int(match.group("units")),
            target_city_id=int(match.group("target")),
        )
    raise InvalidOrderError("Unknown command format.")
