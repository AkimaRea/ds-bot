from __future__ import annotations


class DomainError(ValueError):
    """Base class for game rule violations."""


class GameNotActiveError(DomainError):
    pass


class OrdersLockedError(DomainError):
    pass


class CityNotFoundError(DomainError):
    pass


class TeamNotFoundError(DomainError):
    pass


class OwnershipError(DomainError):
    pass


class InsufficientUnitsError(DomainError):
    pass


class InvalidOrderError(DomainError):
    pass
