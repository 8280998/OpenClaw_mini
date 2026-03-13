from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    prompt_prefix: str
    suggested_mode: str | None = None


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills = self._load_skills()

    def _load_skills(self) -> dict[str, Skill]:
        skills: dict[str, Skill] = {}
        for path in sorted(self.skills_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            skill = Skill(
                name=str(data["name"]).strip(),
                description=str(data["description"]).strip(),
                prompt_prefix=str(data["prompt_prefix"]).strip(),
                suggested_mode=str(data.get("suggested_mode")).strip().lower()
                if data.get("suggested_mode")
                else None,
            )
            skills[skill.name] = skill
        return skills

    def reload(self) -> None:
        self._skills = self._load_skills()

    def list_skills(self) -> list[Skill]:
        return sorted(self._skills.values(), key=lambda item: item.name)

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)
