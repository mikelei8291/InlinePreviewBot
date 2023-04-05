import os
from os.path import expanduser, join
from typing import Any

from yaml import safe_load


class ConfigLoader:
    def __init__(self, config_path: str | None = None):
        if not config_path:
            if os.name == "posix":
                xdg_config_home = os.getenv("XDG_CONFIG_HOME") or expanduser("~/.config")
                config_path = join(xdg_config_home, __package__)
            elif os.name == "nt" and (appdata := os.getenv("appdata")):
                config_path = join(appdata, __package__)
            else:
                config_path = join(expanduser("~"), f".{__package__}")
        self.config_path = config_path

    def load(self) -> dict[str, Any]:
        try:
            with open(join(self.config_path, "config.yaml"), encoding="utf-8") as f:
                return safe_load(f)
        except OSError as e:
            raise RuntimeError(f"Cannot open config file: {e.filename}") from e
