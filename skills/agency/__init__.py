"""
Agency Agents Integration Skill for Hermes.

Provides access to 200+ specialist AI personas from the Agency Agents repository.
Personas are Markdown files with YAML frontmatter, compatible with Claude Code,
Cursor, Copilot, Gemini, OpenCode, and other AI coding tools.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home


AGENCY_REPO_URL = "https://github.com/msitarzewski/agency-agents"
AGENCY_LOCAL_DIR = get_hermes_home() / "skills" / "agency" / "agents"
CACHE_FILE = get_hermes_home() / "skills" / "agency" / "personas_cache.json"


def _ensure_local_repo() -> bool:
    """Clone or update the Agency Agents repository locally."""
    if not AGENCY_LOCAL_DIR.exists():
        AGENCY_LOCAL_DIR.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", AGENCY_REPO_URL, str(AGENCY_LOCAL_DIR)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            return False
    else:
        try:
            subprocess.run(
                ["git", "-C", str(AGENCY_LOCAL_DIR), "pull", "--ff-only"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass  # Non-fatal
    return True


def _load_yaml(text: str) -> Any:
    """Parse YAML with whichever engine the runtime ships (Hermes 0.21.6 ships ruamel.yaml)."""
    try:
        from ruamel.yaml import YAML

        return YAML(typ="safe").load(text)
    except Exception:
        try:
            import yaml

            return yaml.safe_load(text)
        except Exception:
            return None


def _scan_personas() -> list[dict[str, Any]]:
    """Scan local personas directory and return list of persona metadata."""
    if not AGENCY_LOCAL_DIR.exists():
        return []

    personas = []
    for md_file in AGENCY_LOCAL_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                # Parse YAML frontmatter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = _load_yaml(parts[1])
                    if not isinstance(frontmatter, dict):
                        continue
                    frontmatter["_file"] = str(md_file.relative_to(AGENCY_LOCAL_DIR))
                    frontmatter["_content"] = parts[2].strip()
                    personas.append(frontmatter)
        except Exception:
            continue
    return personas


def _build_cache() -> dict[str, Any]:
    """Build and save persona cache."""
    personas = _scan_personas()
    cache = {
        "personas": personas,
        "categories": sorted(set(p.get("category", "uncategorized") for p in personas)),
        "count": len(personas),
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    return cache


def load_personas(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Load personas from cache or rebuild."""
    if force_refresh or not CACHE_FILE.exists():
        _ensure_local_repo()
        return _build_cache()["personas"]

    try:
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return cache["personas"]
    except Exception:
        _ensure_local_repo()
        return _build_cache()["personas"]


def list_personas(
    category: Optional[str] = None,
    search: Optional[str] = None,
    remote: bool = False,
) -> list[dict[str, Any]]:
    """List available personas with optional filtering."""
    if remote:
        # TODO: Implement GitHub API fetch
        return []

    personas = load_personas()

    if category:
        personas = [p for p in personas if p.get("category", "").lower() == category.lower()]

    if search:
        search_lower = search.lower()
        personas = [
            p
            for p in personas
            if search_lower in p.get("name", "").lower()
            or search_lower in p.get("description", "").lower()
            or search_lower in p.get("tags", [])
        ]

    return personas


def get_persona(name: str) -> Optional[dict[str, Any]]:
    """Get a specific persona by name."""
    personas = load_personas()
    for p in personas:
        if p.get("name", "").lower() == name.lower():
            return p
    return None


def format_persona_for_context(persona: dict[str, Any]) -> str:
    """Format persona for injection into conversation context."""
    lines = [
        f"# Persona: {persona.get('name', 'Unknown')}",
        f"**Role**: {persona.get('role', 'Specialist')}",
        f"**Description**: {persona.get('description', '')}",
        "",
        "## Instructions",
        persona.get("_content", "No instructions provided."),
    ]
    return "\n".join(lines)


# CLI command handlers (called by hermes_cli command system)
def cmd_list(args: list[str]) -> str:
    """Handle /agency list command."""
    import argparse
    parser = argparse.ArgumentParser(prog="/agency list")
    parser.add_argument("--category", "-c")
    parser.add_argument("--search", "-s")
    parser.add_argument("--remote", "-r", action="store_true")
    parsed = parser.parse_args(args)

    personas = list_personas(category=parsed.category, search=parsed.search, remote=parsed.remote)

    if not personas:
        return "No personas found. Run `/agency install` first."

    lines = [f"Found {len(personas)} persona(s):"]
    for p in personas[:50]:
        cat = p.get("category", "uncategorized")
        desc = p.get("description", "")[:60]
        lines.append(f"  • {p.get('name', '?')} [{cat}] — {desc}")

    if len(personas) > 50:
        lines.append(f"  ... and {len(personas) - 50} more")
    return "\n".join(lines)


def cmd_use(args: list[str]) -> str:
    """Handle /agency use command."""
    import argparse
    parser = argparse.ArgumentParser(prog="/agency use")
    parser.add_argument("persona")
    parser.add_argument("--context", "-c", default="")
    parsed = parser.parse_args(args)

    persona = get_persona(parsed.persona)
    if not persona:
        return f"Persona '{parsed.persona}' not found. Run `/agency list` to see available."

    context = format_persona_for_context(persona)
    if parsed.context:
        context += f"\n\n## Current Task Context\n{parsed.context}"

    # Store in skill context (will be picked up by agent)
    return f"ACTIVATE_PERSONA::{persona['name']}::\n{context}"


def cmd_install(args: list[str]) -> str:
    """Handle /agency install command."""
    import argparse
    parser = argparse.ArgumentParser(prog="/agency install")
    parser.add_argument("--category", "-c")
    parsed = parser.parse_args(args)

    if _ensure_local_repo():
        cache = _build_cache()
        return f"✅ Installed {cache['count']} personas from {AGENCY_REPO_URL}"
    return "❌ Failed to clone repository"


def cmd_update(args: list[str]) -> str:
    """Handle /agency update command."""
    if _ensure_local_repo():
        cache = _build_cache()
        return f"✅ Updated: {cache['count']} personas"
    return "❌ Failed to update"


def cmd_workflow(args: list[str]) -> str:
    """Handle /agency workflow command."""
    import argparse
    parser = argparse.ArgumentParser(prog="/agency workflow")
    parser.add_argument("name")
    parser.add_argument("personas", nargs="+")
    parsed = parser.parse_args(args)

    # Validate personas exist
    missing = [p for p in parsed.personas if not get_persona(p)]
    if missing:
        return f"❌ Unknown personas: {', '.join(missing)}"

    # Save workflow
    workflows_dir = get_hermes_home() / "skills" / "agency" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    workflow_file = workflows_dir / f"{parsed.name}.json"
    workflow_file.write_text(
        json.dumps({"name": parsed.name, "personas": parsed.personas}, indent=2),
        encoding="utf-8",
    )
    return f"✅ Workflow '{parsed.name}' created with {len(parsed.personas)} personas"


def cmd_run(args: list[str]) -> str:
    """Handle /agency run command."""
    import argparse
    parser = argparse.ArgumentParser(prog="/agency run")
    parser.add_argument("workflow")
    parser.add_argument("--context", "-c", default="")
    parsed = parser.parse_args(args)

    workflows_dir = get_hermes_home() / "skills" / "agency" / "workflows"
    workflow_file = workflows_dir / f"{parsed.workflow}.json"

    if not workflow_file.exists():
        return f"Workflow '{parsed.workflow}' not found. Create with `/agency workflow`."

    workflow = json.loads(workflow_file.read_text(encoding="utf-8"))
    contexts = []
    for persona_name in workflow["personas"]:
        persona = get_persona(persona_name)
        if persona:
            ctx = format_persona_for_context(persona)
            if parsed.context:
                ctx += f"\n\n## Task Context\n{parsed.context}"
            contexts.append(ctx)

    return "WORKFLOW_START::" + "\n\n---\n\n".join(contexts)


def cmd_clear(args: list[str]) -> str:
    """Handle /agency clear command."""
    return "CLEAR_PERSONA::"