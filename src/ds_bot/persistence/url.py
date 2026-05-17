from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse


def sqlite_path_from_url(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Only sqlite database URLs are supported by the local adapter.")
    if parsed.path in ("", "/"):
        raise ValueError("SQLite database URL must include a file path.")
    if parsed.netloc not in ("", "."):
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return Path(unquote(path))
