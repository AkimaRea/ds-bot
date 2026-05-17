from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ds_bot.application.order_service import OrderService
from ds_bot.application.setup_service import SetupService
from ds_bot.application.status_service import StatusService
from ds_bot.application.turn_service import TurnService
from ds_bot.config import Settings
from ds_bot.discord.command_parser import ParsedCommand, parse_command
from ds_bot.discord.permissions import (
    DiscordAccessConfig,
    DiscordContext,
    ensure_host_access,
    ensure_zombie_access,
    resolve_team_id,
)
from ds_bot.domain.enums import OrderType
from ds_bot.domain.errors import DomainError
from ds_bot.persistence.sqlite_repository import SQLiteGameRepository
from ds_bot.persistence.url import sqlite_path_from_url

logger = logging.getLogger(__name__)


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
    access_config = DiscordAccessConfig(
        host_role_id=settings.host_role_id,
        control_channel_id=settings.control_channel_id,
        zombie_channel_id=settings.zombie_channel_id,
    )

    @bot.event
    async def on_ready() -> None:
        logger.info("bot_ready", extra={"user": str(bot.user)})

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.content.startswith("!"):
            return
        if message.content.split(maxsplit=1)[0].lower() in {"!startgame", "!endturn", "!lock"}:
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
            game = setup_service.start_new_game(guild_id=_guild_id(ctx.message, settings))
            await ctx.reply("Game started.")
            await ctx.send(status_service.host_status(guild_id=game.guild_id))
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

    @bot.command(name="endturn")
    async def end_turn(ctx: commands.Context) -> None:
        try:
            ensure_host_access(_context_from_message(ctx.message), access_config)
            turn_service.end_turn(guild_id=_guild_id(ctx.message, settings))
            await ctx.reply("Turn processed.")
            await ctx.send(status_service.host_status(guild_id=_guild_id(ctx.message, settings)))
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
        except Exception as exc:  # noqa: BLE001
            await _reply_error(ctx.message, exc)

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


def _guild_id(message: discord.Message, settings: Settings) -> int | None:
    if settings.discord_guild_id is not None:
        return settings.discord_guild_id
    return message.guild.id if message.guild is not None else None


async def _reply_error(message: discord.Message, exc: Exception) -> None:
    logger.exception("discord_command_failed")
    await message.reply(f"Error: {exc}")


def _required(value: int | None) -> int:
    if value is None:
        raise DomainError("Command is missing a required value.")
    return value
