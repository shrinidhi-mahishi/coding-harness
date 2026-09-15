from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.cwd() / ".agents" / "skills",
    Path.home() / ".agents" / "skills",
]


def find_skills():
    """Map each skill name to its description and SKILL.md path."""
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            _, frontmatter, _ = path.read_text().split("---", 2)
            meta = yaml.safe_load(frontmatter)
            description = " ".join(meta["description"].split())
            skills[meta["name"]] = {"description": description, "path": path}
    return skills


SKILLS = find_skills()


def skills_prompt():
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text()
