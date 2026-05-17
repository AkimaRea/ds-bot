from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord

from ds_bot.discord.buttons import ButtonAction, ButtonId

ButtonCallback = Callable[[discord.Interaction, ButtonId], Awaitable[None]]


class ControlPanelView(discord.ui.View):
    def __init__(
        self,
        game_id: int,
        turn_number: int,
        on_start_game: ButtonCallback,
        on_end_turn: ButtonCallback,
    ) -> None:
        super().__init__(timeout=None)
        self.add_item(
            _ActionButton(
                label="Начало игры",
                style=discord.ButtonStyle.success,
                button_id=ButtonId(ButtonAction.START_GAME, game_id, turn_number),
                callback_handler=on_start_game,
            )
        )
        self.add_item(
            _ActionButton(
                label="Конец хода",
                style=discord.ButtonStyle.danger,
                button_id=ButtonId(ButtonAction.END_TURN, game_id, turn_number),
                callback_handler=on_end_turn,
            )
        )


class TeamOrderView(discord.ui.View):
    def __init__(
        self,
        game_id: int,
        turn_number: int,
        team_id: int,
        on_lock_orders: ButtonCallback,
    ) -> None:
        super().__init__(timeout=None)
        self.add_item(
            _ActionButton(
                label="Отправить приказ",
                style=discord.ButtonStyle.primary,
                button_id=ButtonId(ButtonAction.LOCK_ORDERS, game_id, turn_number, team_id),
                callback_handler=on_lock_orders,
            )
        )


class _ActionButton(discord.ui.Button):
    def __init__(
        self,
        label: str,
        style: discord.ButtonStyle,
        button_id: ButtonId,
        callback_handler: ButtonCallback,
    ) -> None:
        super().__init__(label=label, style=style, custom_id=button_id.render())
        self.button_id = button_id
        self.callback_handler = callback_handler

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.callback_handler(interaction, self.button_id)
