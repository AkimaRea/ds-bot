from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from ds_bot.application.repositories import GameRepository
from ds_bot.domain.serialization import admin_audit_to_dict, battle_to_dict, turn_history_to_dict


class HistoryExportService:
    def __init__(self, repository: GameRepository, export_dir: str | Path = "exports") -> None:
        self.repository = repository
        self.export_dir = Path(export_dir)

    def export_markdown(
        self,
        created_by_user_id: int,
        guild_id: int | None = None,
    ) -> Path:
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Game was not created.")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        path = self.export_dir / f"history-{timestamp}.md"
        path.write_text(_render_markdown(game, created_by_user_id), encoding="utf-8")
        return path

    def export_json(
        self,
        created_by_user_id: int,
        guild_id: int | None = None,
    ) -> Path:
        game = self.repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Game was not created.")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        path = self.export_dir / f"history-{timestamp}.json"
        payload = {
            "created_by_user_id": created_by_user_id,
            "game_id": game.id,
            "guild_id": game.guild_id,
            "turn_history": [turn_history_to_dict(item) for item in game.turn_history],
            "battle_history": [
                battle_to_dict(battle)
                for history in game.turn_history
                for battle in history.battles
            ],
            "admin_audit_log": [admin_audit_to_dict(item) for item in game.admin_audit_log],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def _render_markdown(game, created_by_user_id: int) -> str:
    lines = [
        "# Game History",
        "",
        f"- Game ID: {game.id}",
        f"- Guild ID: {game.guild_id}",
        f"- Exported by: {created_by_user_id}",
        "",
        "## Turns",
    ]
    if not game.turn_history:
        lines.append("")
        lines.append("No processed turns yet.")
    for history in game.turn_history:
        lines.extend(
            [
                "",
                f"### Turn {history.turn_number}",
                "",
                f"Killed units: {history.killed_units}",
                "",
                "Events:",
            ]
        )
        lines.extend(f"- {event}" for event in history.events)
        if history.battles:
            lines.extend(["", "Battles:"])
        for battle in history.battles:
            lines.append(
                "- "
                f"City #{battle.target_city_id}: defender {battle.defender_owner_type.value}, "
                f"attackers {battle.attackers}, winner {battle.winner_owner_type.value}, "
                f"remaining {battle.remaining_units}, killed {battle.killed_units}"
            )

    lines.extend(["", "## Admin Audit"])
    if not game.admin_audit_log:
        lines.append("")
        lines.append("No manual edits.")
    for record in game.admin_audit_log:
        lines.extend(
            [
                "",
                f"### {record.action}",
                "",
                f"- Turn: {record.turn_number}",
                f"- Host user: {record.host_user_id}",
                f"- Before: `{json.dumps(record.before, ensure_ascii=False)}`",
                f"- After: `{json.dumps(record.after, ensure_ascii=False)}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)
