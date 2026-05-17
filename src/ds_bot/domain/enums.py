from __future__ import annotations

from enum import StrEnum


class GameStatus(StrEnum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    FINISHED = "finished"


class OwnerType(StrEnum):
    TEAM = "team"
    BARBARIANS = "barbarians"
    ZOMBIES = "zombies"
    EMPTY = "empty"


class OrderActorType(StrEnum):
    TEAM = "team"
    ZOMBIES = "zombies"


class OrderType(StrEnum):
    ATTACK = "attack"
    MOVE = "move"
    DONATE = "donate"
    UPGRADE = "upgrade"
    ZOMBIE_ATTACK = "zombie_attack"


class TurnPhase(StrEnum):
    MOVEMENT = "movement"
    DONATION = "donation"
    UPGRADE = "upgrade"
    ATTACK = "attack"
    ZOMBIE_ATTACK = "zombie_attack"
    INCOME = "income"
    ZOMBIE_GROWTH = "zombie_growth"
