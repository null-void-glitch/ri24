"""Multi-scoutId routing config.

Models the two-tier setup: one organization-wide scoutId that every advisor
can see, plus one scoutId per advisor for their personal pipeline. The sync
loop iterates over every entry and tags inbound leads with their pool name
so the CRM knows which advisor's inbox they belong in.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).parent
DEFAULT_CONFIG_FILE = ROOT / "config.json"


class Advisor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    scout_id: str


class Organization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    scout_id: Optional[str] = None


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization: Organization
    advisors: list[Advisor] = Field(default_factory=list)

    def pools(self) -> list[tuple[str, str]]:
        """Yield (pool_name, scout_id) for every configured pipeline.

        Pool name is ``"organization"`` for the org-wide scoutId and
        ``"advisor:<name>"`` for each advisor.
        """
        result: list[tuple[str, str]] = []
        if self.organization.scout_id:
            result.append(("organization", self.organization.scout_id))
        for a in self.advisors:
            result.append((f"advisor:{a.name}", a.scout_id))
        return result


def load(path: Path = DEFAULT_CONFIG_FILE) -> Config:
    return Config.model_validate(json.loads(path.read_text()))
