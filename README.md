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

Создайте `.env`:

```text
DISCORD_TOKEN=
DISCORD_GUILD_ID=
HOST_ROLE_ID=
CONTROL_CHANNEL_ID=
ZOMBIE_CHANNEL_ID=
DATABASE_URL=sqlite:///./data/ds_bot.sqlite3
LOG_LEVEL=INFO
```

Запуск:

```powershell
python -m ds_bot.main
```

## Команды первого среза

- `!startgame` в канале управления: сбросить и начать игру.
- `!endturn` в канале управления: обработать текущий ход.
- `!lock` в командном канале: зафиксировать приказы команды.
- `!attack 50 1 в 8`: атака.
- `!move 30 1 в 2`: перемещение.
- `!donate 40 1 в 9`: донат.
- `!up 1`: повышение замка.
- `!zattack 50 8`: атака зомби из зомби-канала.

Уже реализованы доменное ядро, application-сервисы, SQLite-сохранение, текстовый
Discord-адаптер, административное редактирование и экспорт истории.
