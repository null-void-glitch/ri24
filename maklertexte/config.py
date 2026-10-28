"""Lädt Zugangsdaten, OpenAI-Key und das Region-Mapping aus der .env.

Die .env enthält neben einfachen KEY = value-Zeilen ein mehrzeiliges
Python-Dict (region_mapping), das Standard-Dotenv-Parser nicht verstehen.
Daher parsen wir bewusst selbst.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")


def _read_env(text: str) -> dict[str, str]:
    """Einfache KEY = value-Zeilen (ohne das mehrzeilige Dict) einlesen."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # nur echte "KEY = value"-Zeilen; das Dict beginnt mit "region_mapping ="
        # und wird separat behandelt.
        if stripped.startswith("region_mapping"):
            break
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _read_region_mapping(text: str) -> dict[str, str]:
    """Das mehrzeilige `region_mapping = { ... }`-Dict per AST sicher parsen."""
    match = re.search(r"region_mapping\s*=\s*(\{.*\})", text, re.DOTALL)
    if not match:
        return {}
    return ast.literal_eval(match.group(1))


def load_config(env_path: Path = ENV_PATH) -> "Config":
    text = env_path.read_text(encoding="utf-8")
    values = _read_env(text)
    return Config(
        username=values["USERNAME"],
        password=values["PASSWORD"],
        openai_key=values["OPENAI_KEY"],
        region_mapping=_read_region_mapping(text),
    )


class Config:
    def __init__(
        self,
        username: str,
        password: str,
        openai_key: str,
        region_mapping: dict[str, str],
    ) -> None:
        self.username = username
        self.password = password
        self.openai_key = openai_key
        self.region_mapping = region_mapping


if __name__ == "__main__":
    cfg = load_config()
    print(f"USERNAME: {cfg.username}")
    print(f"OPENAI_KEY gesetzt: {bool(cfg.openai_key)} (len={len(cfg.openai_key)})")
    print(f"Regionen im Mapping: {len(cfg.region_mapping)}")
    # Beispielhaft die ersten drei Einträge zeigen.
    for code, name in list(cfg.region_mapping.items())[:3]:
        print(f"  {code} -> {name}")
