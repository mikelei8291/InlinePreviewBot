import os
from os.path import expanduser, isfile, join
from typing import Any

from yaml import safe_load


class ConfigLoader:
    _FILENAME = "config.yaml"

    def __init__(self, config_path: str | None = None):
        if not config_path:
            if os.name == "posix":
                paths = [join(path, __package__, self._FILENAME) for path in (
                    os.getenv("XDG_CONFIG_HOME") or expanduser("~/.config"),  # user config
                    "/etc"  # system config
                )]
            elif os.name == "nt" and (appdata := os.getenv("appdata")):
                paths = [join(appdata, __package__, self._FILENAME)]
            else:
                paths = [join(expanduser("~"), f".{__package__}", self._FILENAME)]
            try:
                config_path = next(filter(isfile, paths))
            except StopIteration:
                raise RuntimeError(f"Config file not found in any one of the locations: {paths}")
        self.config_path = config_path

    def load(self) -> dict[str, Any]:
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return safe_load(f)
        except OSError as e:
            raise RuntimeError(f"Cannot open config file: {e.filename}") from e
