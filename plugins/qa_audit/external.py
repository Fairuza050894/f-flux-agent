"""``/veriflow``, ``/autodev`` and ``/agency`` handlers, moved out of ``cli.py``.

The core fork registered these as in-session slash commands backed by instance methods on
``HermesCLI`` (plus ``CommandDef`` rows). Here they are ordinary plugin command handlers that return
the same user-facing text instead of printing it; the CLI and the messaging gateway both render the
returned string.
"""

from __future__ import annotations

import json
import shlex

from .skill_bridge import load_skill_module

_VERIFLOW_USAGE = "\n".join(
    [
        "Usage: /veriflow <run|status|report|wait|list|config> [args...]",
        "  Examples:",
        "    /veriflow run --repo https://github.com/owner/repo",
        "    /veriflow status <run_id>",
        "    /veriflow report <run_id> --format markdown",
        "    /veriflow wait <run_id> --timeout 300",
        "    /veriflow list",
        "    /veriflow config",
    ]
)

_AUTODEV_USAGE = "\n".join(
    [
        "Usage: /autodev <create|status|logs|artifacts|url|approve|reject|list> [args...]",
        "  Examples:",
        '    /autodev create "Build a landing page for dentist clinic. Email me@test.com"',
        "    /autodev status <project_id>",
        "    /autodev logs <project_id>",
        "    /autodev url <project_id>",
        "    /autodev approve <project_id> --gate proposal",
        "    /autodev list --status running",
    ]
)

_AGENCY_USAGE = "\n".join(
    [
        "Usage: /agency <list|use|install|update|workflow|run|clear> [args...]",
        "  Examples:",
        "    /agency list --category engineering",
        '    /agency use backend-architect --context "design API for user service"',
        "    /agency install",
        "    /agency workflow qa-team qa-automation-lead test-architect",
        '    /agency run qa-team --context "test checkout flow"',
        "    /agency clear",
    ]
)

_VERIFLOW_FUNCS = {
    "run": "cmd_run",
    "status": "cmd_status",
    "report": "cmd_report",
    "wait": "cmd_wait",
    "list": "cmd_list",
    "config": "cmd_config",
}

_AUTODEV_FUNCS = {
    "create": "cmd_create",
    "status": "cmd_status",
    "logs": "cmd_logs",
    "artifacts": "cmd_artifacts",
    "url": "cmd_url",
    "approve": "cmd_approve",
    "reject": "cmd_reject",
    "list": "cmd_list",
}

_AGENCY_FUNCS = {
    "list": "cmd_list",
    "use": "cmd_use",
    "install": "cmd_install",
    "update": "cmd_update",
    "workflow": "cmd_workflow",
    "run": "cmd_run",
    "clear": "cmd_clear",
}


def _split_args(raw_args: str) -> tuple[str, str]:
    """``(subcommand, remainder)``; ``("", "")`` when no subcommand was given."""
    parts = (raw_args or "").split(None, 1)
    if not parts:
        return "", ""
    return parts[0], (parts[1] if len(parts) > 1 else "")


def _invoke(skill: str, label: str, funcs: dict[str, str], subcmd: str, args: str) -> tuple[str, str]:
    """Import *skill*, call the mapped ``cmd_*`` function and return ``(subcmd, raw_result)``.

    ``("", message)`` signals a terminal message to render as-is; ``(subcmd, "")`` signals a
    ``SystemExit`` (the skill prints its own usage), which produces no plugin output.
    """
    try:
        module = load_skill_module(skill)
    except ImportError as exc:
        return "", f"{label} skill not available: {exc}"

    func_name = funcs.get(subcmd)
    if func_name is None:
        return "", f"Unknown {label.lower()} subcommand: {subcmd}"

    arg_list = shlex.split(args) if args else []
    try:
        return subcmd, getattr(module, func_name)(arg_list)
    except SystemExit:
        return "", ""
    except Exception as exc:  # surfaced to the user as the old CLI handler did
        return "", f"{label} error: {exc}"


def handle_veriflow(raw_args: str) -> str:
    """Handle ``/veriflow <subcommand> [args...]``."""
    subcmd, args = _split_args(raw_args)
    if not subcmd:
        return _VERIFLOW_USAGE

    subcmd, result = _invoke("veriflow_trigger", "Veriflow", _VERIFLOW_FUNCS, subcmd, args)
    if not subcmd:
        return result

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return result

    if not data.get("success"):
        return f"❌ {data.get('error', 'Unknown error')}"

    if subcmd == "run":
        return (
            f"✅ {data.get('message', 'Run started')}\n"
            f"   Run ID: {data.get('run_id')}\n"
            f"   Monitor: {data.get('monitor_url')}"
        )
    if subcmd == "status":
        lines = [f"Run {data.get('id')}: {data.get('status', 'unknown')}"]
        if data.get("progress"):
            lines.append(f"Progress: {data['progress']}")
        return "\n".join(lines)
    if subcmd == "report":
        content = data.get("content", "")
        fmt = data.get("format", "markdown")
        if fmt == "markdown":
            return content
        if fmt == "html":
            return f"HTML report ({len(content)} chars) - open in browser"
        return json.dumps(data, indent=2)
    if subcmd == "wait":
        return f"✅ Run completed: {data.get('status')}"
    if subcmd == "list":
        runs = data.get("runs", [])
        if not runs:
            return "No runs found."
        lines = [
            f"  {r.get('id')} | {r.get('status')} | {r.get('project_name', '?')}" for r in runs[:10]
        ]
        if len(runs) > 10:
            lines.append(f"  ... and {len(runs) - 10} more")
        return "\n".join(lines)
    if subcmd == "config":
        return json.dumps(data, indent=2)
    return result


def handle_autodev(raw_args: str) -> str:
    """Handle ``/autodev <subcommand> [args...]``."""
    subcmd, args = _split_args(raw_args)
    if not subcmd:
        return _AUTODEV_USAGE

    subcmd, result = _invoke("autodev_launcher", "AutoDev", _AUTODEV_FUNCS, subcmd, args)
    if not subcmd:
        return result

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return result

    if not data.get("success"):
        return f"❌ {data.get('error', 'Unknown error')}"

    if subcmd == "create":
        return (
            f"✅ {data.get('message', 'Project created')}\n"
            f"   Project ID: {data.get('project_id')}\n"
            f"   Dashboard: {data.get('dashboard_url')}"
        )
    if subcmd == "status":
        proj = data.get("project", {})
        lines = [
            f"Project {proj.get('id')}: {proj.get('status')}",
            f"Brief: {proj.get('brief', '')[:80]}...",
        ]
        if data.get("dag"):
            dag = data["dag"]
            lines.append(f"DAG: {len(dag.get('nodes', []))} nodes, {len(dag.get('edges', []))} edges")
        return "\n".join(lines)
    if subcmd == "logs":
        return data.get("logs", "No logs")
    if subcmd == "artifacts":
        arts = data.get("artifacts", [])
        if not arts:
            return "No artifacts."
        return "\n".join(
            f"  {a.get('type')}: {a.get('name')} ({a.get('size', 0)} bytes)" for a in arts[:10]
        )
    if subcmd == "url":
        lines = [f"Staging URL: {data.get('url')}"]
        if data.get("health"):
            lines.append(f"Health: {data['health']}")
        return "\n".join(lines)
    if subcmd in ("approve", "reject"):
        return f"✅ Gate {subcmd}d: {data.get('gate', '?')}"
    if subcmd == "list":
        projs = data.get("projects", [])
        if not projs:
            return "No projects."
        return "\n".join(
            f"  {p.get('id')} | {p.get('status')} | {p.get('brief', '')[:50]}..." for p in projs[:10]
        )
    return result


def handle_agency(raw_args: str) -> str:
    """Handle ``/agency <subcommand> [args...]``."""
    subcmd, args = _split_args(raw_args)
    if not subcmd:
        return _AGENCY_USAGE

    _subcmd, result = _invoke("agency", "Agency", _AGENCY_FUNCS, subcmd, args)
    return result
