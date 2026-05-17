# ds-bot

Локально хостимый Discord-бот для пошаговой стратегии из `TECHNICAL_SPEC.md`.

## Разработка

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

Пока реализован первый вертикальный срез домена: стартовая карта, валидация приказов,
резервы юнитов, обработка хода и текстовые статусы без привязки к Discord.
