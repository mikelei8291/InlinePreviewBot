import os
from pathlib import Path
from typing import Any

from telebot import logger
from yaml import safe_load


class ConfigLoader:
    _FILENAME = "config.yaml"

    def __init__(self, config_path: Path | None = None):
        if not config_path:
            if os.name == "posix":
                paths = [Path(path).expanduser() / __package__ / self._FILENAME for path in (
                    os.getenv("XDG_CONFIG_HOME") or "~/.config",  # user config
                    "/etc"  # system config
                )]
            elif os.name == "nt" and (appdata := os.getenv("appdata")):
                paths = [Path(appdata) / __package__ / self._FILENAME]
            else:
                paths = [Path("~").expanduser() / f".{__package__}" / self._FILENAME]
            try:
                config_path = next(p for p in paths if p.is_file())
            except StopIteration:
                raise RuntimeError(f"Config file not found in any one of the locations: {list(map(str, paths))}")
        self.config_path = config_path

    def load(self) -> dict[str, Any]:
        try:
            with self.config_path.open(encoding="utf-8") as f:
                return safe_load(f)
        except OSError as e:
            raise RuntimeError(f"Cannot open config file: {e.filename}") from e
