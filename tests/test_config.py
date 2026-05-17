from __future__ import annotations

from ds_bot.config import Settings


def test_settings_load_team_discord_ids(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "token")
    monkeypatch.setenv("TEAM_1_ROLE_ID", "101")
    monkeypatch.setenv("TEAM_1_CHANNEL_ID", "201")

    settings = Settings.from_env()

    assert settings.discord_token == "token"
    assert settings.teams[0].team_id == 1
    assert settings.teams[0].role_id == 101
    assert settings.teams[0].channel_id == 201
    assert settings.teams[1].team_id == 2
    assert settings.teams[1].role_id is None
