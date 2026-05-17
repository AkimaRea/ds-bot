from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from ds_bot.application.admin_edit_service import AdminEditService
from ds_bot.application.history_export_service import HistoryExportService
from ds_bot.application.order_service import OrderService
from ds_bot.application.setup_service import SetupService
from ds_bot.application.status_service import StatusService
from ds_bot.application.turn_service import TurnService
from ds_bot.config import Settings, TeamDiscordSettings
from ds_bot.discord.buttons import ButtonId, ensure_fresh_button
from ds_bot.discord.command_parser import ParsedCommand, parse_command
from ds_bot.discord.permissions import (
    DiscordAccessConfig,
    DiscordContext,
    ensure_host_access,
    ensure_zombie_access,
    resolve_team_id,
)
from ds_bot.discord.views import ControlPanelView, TeamOrderView
from ds_bot.domain.enums import GameStatus, OrderType, OwnerType
from ds_bot.domain.errors import DomainError
from ds_bot.domain.models import GameState
from ds_bot.persistence.sqlite_repository import SQLiteGameRepository
from ds_bot.persistence.url import sqlite_path_from_url

logger = logging.getLogger(__name__)
DOMAIN_COMMANDS = {"!attack", "!move", "!donate", "!up", "!zattack"}


def create_bot(settings: Settings) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    repository = SQLiteGameRepository(sqlite_path_from_url(settings.database_url))
    setup_service = SetupService(repository)
    order_service = OrderService(repository)
    turn_service = TurnService(repository)
    status_service = StatusService(repository)
    admin_service = AdminEditService(repository)
    export_service = HistoryExportService(repository)
    access_config = DiscordAccessConfig(
        host_role_id=settings.host_role_id,
        control_channel_id=settings.control_channel_id,
        zombie_channel_id=settings.zombie_channel_id,
    )

    @bot.event
    async def on_ready() -> None:
        logger.info("bot_ready", extra={"user": str(bot.user)})
        if getattr(bot, "_ds_views_registered", False):
            return
        game = repository.get_active_game(settings.discord_guild_id)
        if game is not None:
            bot.add_view(
                ControlPanelView(game.id, game.current_turn, on_start_button, on_end_turn_button)
            )
            for team in game.teams.values():
                bot.add_view(
                    TeamOrderView(
                        game.id,
                        game.current_turn,
                        team.id,
                        on_lock_orders_button,
                    )
                )
        setattr(bot, "_ds_views_registered", True)

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.content.startswith("!"):
            return
        if message.content.split(maxsplit=1)[0].lower() not in DOMAIN_COMMANDS:
            await bot.process_commands(message)
            return
        await _handle_text_command(
            message,
            settings,
            access_config,
            order_service,
            status_service,
            repository,
        )

    @bot.command(name="startgame")
    async def start_game(ctx: commands.Context) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            game = setup_service.start_new_game(
                guild_id=_guild_id(ctx.message, settings),
                team_discord=_team_discord_map(settings.teams),
            )
            await ctx.reply("Game started.")
            await _publish_all_statuses(
                bot,
                game,
                status_service,
                access_config,
                control_fallback=ctx.channel,
                with_views=True,
                on_start_game=on_start_button,
                on_end_turn=on_end_turn_button,
                on_lock_orders=on_lock_orders_button,
            )
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="endturn")
    async def end_turn(ctx: commands.Context) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            turn_service.end_turn(guild_id=_guild_id(ctx.message, settings))
            await ctx.reply("Turn processed.")
            game = repository.get_active_game(_guild_id(ctx.message, settings))
            if game is not None:
                await _publish_all_statuses(
                    bot,
                    game,
                    status_service,
                    access_config,
                    control_fallback=ctx.channel,
                    with_views=True,
                    on_start_game=on_start_button,
                    on_end_turn=on_end_turn_button,
                    on_lock_orders=on_lock_orders_button,
                )
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="lock")
    async def lock_orders(ctx: commands.Context) -> None:
        try:
            game = repository.get_active_game(_guild_id(ctx.message, settings))
            if game is None:
                raise RuntimeError("Game was not created.")
            team_id = resolve_team_id(game, _context_from_message(ctx.message))
            order_service.lock_orders(team_id, guild_id=_guild_id(ctx.message, settings))
            await ctx.reply("Orders locked.")
            await ctx.send(status_service.team_status(team_id, guild_id=_guild_id(ctx.message, settings)))
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="panel")
    async def panel(ctx: commands.Context) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            game = repository.get_active_game(_guild_id(ctx.message, settings))
            game_id = game.id if game is not None else 0
            turn_number = game.current_turn if game is not None else 0
            await ctx.send(
                "Control panel",
                view=ControlPanelView(game_id, turn_number, on_start_button, on_end_turn_button),
            )
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="admin_owner")
    async def admin_owner(
        ctx: commands.Context,
        city_id: int,
        owner_type: str,
        owner_team_id: int | None = None,
    ) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            admin_service.set_city_owner(
                city_id=city_id,
                owner_type=OwnerType(owner_type),
                owner_team_id=owner_team_id,
                host_user_id=ctx.author.id,
                guild_id=_guild_id(ctx.message, settings),
            )
            await _reply_admin_update(ctx, status_service, settings)
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="admin_units")
    async def admin_units(ctx: commands.Context, city_id: int, units: int) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            admin_service.set_city_units(
                city_id=city_id,
                units=units,
                host_user_id=ctx.author.id,
                guild_id=_guild_id(ctx.message, settings),
            )
            await _reply_admin_update(ctx, status_service, settings)
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="admin_castle")
    async def admin_castle(ctx: commands.Context, city_id: int, castle_level: int) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            admin_service.set_castle_level(
                city_id=city_id,
                castle_level=castle_level,
                host_user_id=ctx.author.id,
                guild_id=_guild_id(ctx.message, settings),
            )
            await _reply_admin_update(ctx, status_service, settings)
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="admin_turn")
    async def admin_turn(ctx: commands.Context, current_turn: int) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            admin_service.set_current_turn(
                current_turn=current_turn,
                host_user_id=ctx.author.id,
                guild_id=_guild_id(ctx.message, settings),
            )
            await _reply_admin_update(ctx, status_service, settings)
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="admin_status")
    async def admin_status(ctx: commands.Context, status: str) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            admin_service.set_game_status(
                status=GameStatus(status),
                host_user_id=ctx.author.id,
                guild_id=_guild_id(ctx.message, settings),
            )
            await _reply_admin_update(ctx, status_service, settings)
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="export")
    async def export_history(ctx: commands.Context, export_format: str = "md") -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            if export_format.lower() == "json":
                path = export_service.export_json(ctx.author.id, _guild_id(ctx.message, settings))
            else:
                path = export_service.export_markdown(
                    ctx.author.id,
                    _guild_id(ctx.message, settings),
                )
            await ctx.reply("History exported.", file=discord.File(Path(path)))
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    async def on_start_button(interaction: discord.Interaction, button_id: ButtonId) -> None:
        try:
            if interaction.message is None:
                raise RuntimeError("Interaction has no message.")
            ensure_host_access(_context_from_interaction(interaction), access_config)
            game = setup_service.start_new_game(
                guild_id=_guild_id_from_interaction(interaction, settings),
                team_discord=_team_discord_map(settings.teams),
            )
            await interaction.response.send_message("Game started.", ephemeral=True)
            await _publish_all_statuses(
                bot,
                game,
                status_service,
                access_config,
                control_fallback=interaction.channel,
                with_views=True,
                on_start_game=on_start_button,
                on_end_turn=on_end_turn_button,
                on_lock_orders=on_lock_orders_button,
            )
        except Exception as exc:  # noqa: BLE001
            await _interaction_error(interaction, exc)

    async def on_end_turn_button(interaction: discord.Interaction, button_id: ButtonId) -> None:
        try:
            ensure_host_access(_context_from_interaction(interaction), access_config)
            game = repository.get_active_game(_guild_id_from_interaction(interaction, settings))
            if game is None:
                raise RuntimeError("Game was not created.")
            ensure_fresh_button(button_id, game.current_turn)
            turn_service.end_turn(guild_id=game.guild_id)
            updated_game = repository.get_active_game(game.guild_id)
            if updated_game is None:
                raise RuntimeError("Game was not found after turn processing.")
            await interaction.response.send_message("Turn processed.", ephemeral=True)
            await _publish_all_statuses(
                bot,
                updated_game,
                status_service,
                access_config,
                control_fallback=interaction.channel,
                with_views=True,
                on_start_game=on_start_button,
                on_end_turn=on_end_turn_button,
                on_lock_orders=on_lock_orders_button,
            )
        except Exception as exc:  # noqa: BLE001
            await _interaction_error(interaction, exc)

    async def on_lock_orders_button(interaction: discord.Interaction, button_id: ButtonId) -> None:
        try:
            context = _context_from_interaction(interaction)
            game = repository.get_active_game(_guild_id_from_interaction(interaction, settings))
            if game is None:
                raise RuntimeError("Game was not created.")
            ensure_fresh_button(button_id, game.current_turn)
            team_id = button_id.team_id or resolve_team_id(game, context)
            resolved_team_id = resolve_team_id(game, context)
            if resolved_team_id != team_id:
                raise DomainError("Button belongs to another team.")
            order_service.lock_orders(team_id, guild_id=game.guild_id)
            await interaction.response.send_message("Orders locked.", ephemeral=True)
            channel = interaction.channel
            if isinstance(channel, discord.abc.Messageable):
                await channel.send(
                    status_service.team_status(team_id, guild_id=game.guild_id),
                    view=TeamOrderView(game.id, game.current_turn, team_id, on_lock_orders_button),
                )
        except Exception as exc:  # noqa: BLE001
            await _interaction_error(interaction, exc)

    return bot


async def _handle_text_command(
    message: discord.Message,
    settings: Settings,
    access_config: DiscordAccessConfig,
    order_service: OrderService,
    status_service: StatusService,
    repository,
) -> None:
    try:
        parsed = parse_command(message.content)
        guild_id = _guild_id(message, settings)
        game = repository.get_active_game(guild_id)
        if game is None:
            raise RuntimeError("Game was not created.")

        if parsed.type == OrderType.ZOMBIE_ATTACK:
            ensure_zombie_access(_context_from_message(message), access_config)
            _apply_zombie_order(order_service, parsed, guild_id)
            await message.reply("Zombie order saved.")
            return

        team_id = resolve_team_id(game, _context_from_message(message))
        _apply_team_order(order_service, team_id, parsed, guild_id)
        await message.reply("Order saved.")
        await message.channel.send(status_service.team_status(team_id, guild_id=guild_id))
    except Exception as exc:  # noqa: BLE001
        await _reply_error(message, exc)


def _apply_team_order(
    order_service: OrderService,
    team_id: int,
    parsed: ParsedCommand,
    guild_id: int | None,
) -> None:
    if parsed.type == OrderType.ATTACK:
        order_service.add_attack(
            team_id,
            _required(parsed.units),
            _required(parsed.source_city_id),
            _required(parsed.target_city_id),
            guild_id,
        )
    elif parsed.type == OrderType.MOVE:
        order_service.add_move(
            team_id,
            _required(parsed.units),
            _required(parsed.source_city_id),
            _required(parsed.target_city_id),
            guild_id,
        )
    elif parsed.type == OrderType.DONATE:
        order_service.add_donate(
            team_id,
            _required(parsed.units),
            _required(parsed.source_city_id),
            _required(parsed.target_city_id),
            guild_id,
        )
    elif parsed.type == OrderType.UPGRADE:
        order_service.add_upgrade(team_id, _required(parsed.city_id), guild_id)
    else:
        raise DomainError("Unsupported team command.")


def _apply_zombie_order(
    order_service: OrderService,
    parsed: ParsedCommand,
    guild_id: int | None,
) -> None:
    order_service.add_zombie_attack(
        _required(parsed.units),
        _required(parsed.target_city_id),
        guild_id,
    )


def _context_from_message(message: discord.Message) -> DiscordContext:
    role_ids = frozenset(getattr(role, "id", 0) for role in getattr(message.author, "roles", []))
    return DiscordContext(
        user_id=message.author.id,
        channel_id=message.channel.id,
        role_ids=role_ids,
    )


def _context_from_interaction(interaction: discord.Interaction) -> DiscordContext:
    role_ids = frozenset(getattr(role, "id", 0) for role in getattr(interaction.user, "roles", []))
    channel_id = interaction.channel.id if interaction.channel is not None else 0
    return DiscordContext(
        user_id=interaction.user.id,
        channel_id=channel_id,
        role_ids=role_ids,
    )


def _guild_id(message: discord.Message, settings: Settings) -> int | None:
    if settings.discord_guild_id is not None:
        return settings.discord_guild_id
    return message.guild.id if message.guild is not None else None


def _guild_id_from_interaction(
    interaction: discord.Interaction,
    settings: Settings,
) -> int | None:
    if settings.discord_guild_id is not None:
        return settings.discord_guild_id
    return interaction.guild.id if interaction.guild is not None else None


def _team_discord_map(
    teams: tuple[TeamDiscordSettings, ...],
) -> dict[int, tuple[int | None, int | None]]:
    return {team.team_id: (team.role_id, team.channel_id) for team in teams}


async def _publish_all_statuses(
    bot: commands.Bot,
    game: GameState,
    status_service: StatusService,
    access_config: DiscordAccessConfig,
    control_fallback,
    *,
    with_views: bool,
    on_start_game=None,
    on_end_turn=None,
    on_lock_orders=None,
) -> None:
    control_channel = await _resolve_messageable_channel(
        bot,
        access_config.control_channel_id,
        control_fallback,
    )
    if control_channel is not None:
        await control_channel.send(
            status_service.host_status(guild_id=game.guild_id),
            view=(
                ControlPanelView(game.id, game.current_turn, on_start_game, on_end_turn)
                if with_views and on_start_game is not None and on_end_turn is not None
                else None
            ),
        )
    for team in game.teams.values():
        if team.discord_channel_id is None:
            continue
        team_channel = await _resolve_messageable_channel(bot, team.discord_channel_id, None)
        if team_channel is not None:
            await team_channel.send(
                status_service.team_status(team.id, guild_id=game.guild_id),
                view=(
                    TeamOrderView(game.id, game.current_turn, team.id, on_lock_orders)
                    if with_views and on_lock_orders is not None and game.status == GameStatus.ACTIVE
                    else None
                ),
            )
    if access_config.zombie_channel_id is not None:
        zombie_channel = await _resolve_messageable_channel(
            bot,
            access_config.zombie_channel_id,
            None,
        )
        if zombie_channel is not None:
            await zombie_channel.send(status_service.zombie_status(guild_id=game.guild_id))


async def _resolve_messageable_channel(
    bot: commands.Bot,
    channel_id: int | None,
    fallback,
):
    if channel_id is None:
        return fallback if isinstance(fallback, discord.abc.Messageable) else None
    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)
    return channel if isinstance(channel, discord.abc.Messageable) else None


async def _reply_admin_update(
    ctx: commands.Context,
    status_service: StatusService,
    settings: Settings,
) -> None:
    await ctx.reply("State updated.")
    await ctx.send(status_service.host_status(guild_id=_guild_id(ctx.message, settings)))


async def _reply_error(message: discord.Message, exc: Exception) -> None:
    logger.exception("discord_command_failed")
    await message.reply(f"Error: {exc}")


async def _interaction_error(interaction: discord.Interaction, exc: Exception) -> None:
    logger.exception("discord_interaction_failed")
    content = f"Error: {exc}"
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=True)
    else:
        await interaction.response.send_message(content, ephemeral=True)


def _required(value: int | None) -> int:
    if value is None:
        raise DomainError("Command is missing a required value.")
    return value
