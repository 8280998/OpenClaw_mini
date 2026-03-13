from pathlib import Path

from openclawish.skills import SkillRegistry


def test_skill_registry_loads_json_skills(tmp_path: Path) -> None:
    (tmp_path / "repo.json").write_text(
        '{"name":"repo","description":"desc","prompt_prefix":"prefix","suggested_mode":"workspace"}',
        encoding="utf-8",
    )
    registry = SkillRegistry(tmp_path)
    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0].name == "repo"
