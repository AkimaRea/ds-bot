from __future__ import annotations

from ds_bot.application.admin_edit_service import AdminEditService
from ds_bot.application.history_export_service import HistoryExportService
from ds_bot.application.repositories import InMemoryGameRepository
from ds_bot.application.setup_service import SetupService
from ds_bot.domain.enums import GameStatus, OwnerType


def test_admin_edit_writes_audit_record() -> None:
    repository = InMemoryGameRepository()
    SetupService(repository).start_new_game(guild_id=42)
    admin = AdminEditService(repository)

    admin.set_city_owner(
        city_id=4,
        owner_type=OwnerType.TEAM,
        owner_team_id=1,
        host_user_id=777,
        guild_id=42,
    )
    admin.set_city_units(city_id=4, units=25, host_user_id=777, guild_id=42)
    admin.set_game_status(GameStatus.FINISHED, host_user_id=777, guild_id=42)

    game = repository.get_active_game(guild_id=42)
    assert game is not None
    assert game.cities[4].owner_team_id == 1
    assert game.cities[4].units == 25
    assert game.status == GameStatus.FINISHED
    assert [record.action for record in game.admin_audit_log] == [
        "set_city_owner",
        "set_city_units",
        "set_game_status",
    ]


def test_history_export_creates_markdown_file(tmp_path) -> None:
    repository = InMemoryGameRepository()
    SetupService(repository).start_new_game(guild_id=42)
    AdminEditService(repository).set_city_units(
        city_id=1,
        units=150,
        host_user_id=777,
        guild_id=42,
    )
    service = HistoryExportService(repository, export_dir=tmp_path)

    path = service.export_markdown(created_by_user_id=777, guild_id=42)

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "# Game History" in content
    assert "set_city_units" in content
