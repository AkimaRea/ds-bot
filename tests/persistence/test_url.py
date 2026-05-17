from __future__ import annotations

from ds_bot.persistence.url import sqlite_path_from_url


def test_sqlite_path_from_relative_url() -> None:
    assert str(sqlite_path_from_url("sqlite:///./data/ds_bot.sqlite3")).endswith(
        "data\\ds_bot.sqlite3"
    ) or str(sqlite_path_from_url("sqlite:///./data/ds_bot.sqlite3")).endswith(
        "data/ds_bot.sqlite3"
    )
