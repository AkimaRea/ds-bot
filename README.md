# ds-bot

Локально хостимый Discord-бот для пошаговой стратегии из `TECHNICAL_SPEC.md`.

## Разработка

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

## Локальный запуск

Создайте `.env` по примеру `.env.example`:

```text
DISCORD_TOKEN=
DISCORD_GUILD_ID=
HOST_ROLE_ID=
CONTROL_CHANNEL_ID=
ZOMBIE_CHANNEL_ID=
TEAM_1_ROLE_ID=
TEAM_1_CHANNEL_ID=
TEAM_2_ROLE_ID=
TEAM_2_CHANNEL_ID=
TEAM_3_ROLE_ID=
TEAM_3_CHANNEL_ID=
TEAM_4_ROLE_ID=
TEAM_4_CHANNEL_ID=
TEAM_5_ROLE_ID=
TEAM_5_CHANNEL_ID=
TEAM_6_ROLE_ID=
TEAM_6_CHANNEL_ID=
TEAM_7_ROLE_ID=
TEAM_7_CHANNEL_ID=
TEAM_8_ROLE_ID=
TEAM_8_CHANNEL_ID=
DATABASE_URL=sqlite:///./data/ds_bot.sqlite3
LOG_LEVEL=INFO
```

Запуск:

```powershell
python -m ds_bot.main
```

## Команды

- `!panel` в канале управления: опубликовать кнопки управления.
- `!startgame` в канале управления: сбросить и начать игру.
- `!endturn` в канале управления: обработать текущий ход.
- `!lock` в командном канале: зафиксировать приказы команды.
- `!attack 50 1 в 8`: атака.
- `!move 30 1 в 2`: перемещение.
- `!donate 40 1 в 9`: донат.
- `!up 1`: повышение замка.
- `!zattack 50 8`: атака зомби из зомби-канала.
- `!admin_owner 4 team 1`: передать город #4 команде #1.
- `!admin_units 4 25`: изменить количество юнитов города.
- `!admin_castle 4 2`: изменить уровень замка.
- `!admin_turn 3`: изменить текущий ход.
- `!admin_status active`: изменить статус игры.
- `!export md` или `!export json`: экспорт истории.

## Состояние реализации

Реализованы доменное ядро, application-сервисы, SQLite-сохранение, текстовый
Discord-адаптер, Discord-кнопки, публикация статусов по каналам,
административное редактирование, экспорт истории и файловое логирование.
