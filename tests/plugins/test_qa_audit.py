"""Guards the fork's QA command surface, which lives in ``plugins/qa_audit``.

These commands used to be patched straight into ``cli.py``, ``gateway/run.py`` and
``gateway/run_inbound.py``; they are plugin-registered now, so this plugin is the single place that
must keep working on top of upstream 0.21.6. A silent upstream change to the plugin API, or a
rename here, would otherwise drop the whole fork surface without a failing test.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "plugins" / "qa_audit"

EXPECTED_COMMANDS = {
    "audit-qa",
    "qa-audit",
    "check-landing-page",
    "veriflow",
    "vf",
    "autodev",
    "ad",
    "agency",
    "ag",
}


class _RecordingContext:
    """Minimal plugin context that records ``register_command`` calls."""

    def __init__(self) -> None:
        self.commands: dict[str, object] = {}
        self.args_hints: dict[str, str] = {}

    def register_command(self, name, handler=None, description="", args_hint="", **_kwargs):
        self.commands[name] = handler
        self.args_hints[name] = args_hint


@pytest.fixture(scope="module")
def plugin():
    spec = importlib.util.spec_from_file_location(
        "qa_audit_under_test",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture(scope="module")
def parser(plugin):
    return sys.modules[f"{plugin.__name__}.parser"]


def test_registers_the_whole_fork_command_surface(plugin):
    ctx = _RecordingContext()
    plugin.register(ctx)

    assert set(ctx.commands) == EXPECTED_COMMANDS
    assert all(callable(handler) for handler in ctx.commands.values())


def test_audit_spellings_share_one_handler(plugin):
    ctx = _RecordingContext()
    plugin.register(ctx)

    assert ctx.commands["audit-qa"] is ctx.commands["qa-audit"]
    assert ctx.args_hints["audit-qa"]  # adapters surface an argument field for the audit command


def test_command_alias_pairs_share_one_handler(plugin):
    ctx = _RecordingContext()
    plugin.register(ctx)

    assert ctx.commands["vf"] is ctx.commands["veriflow"]
    assert ctx.commands["ad"] is ctx.commands["autodev"]
    assert ctx.commands["ag"] is ctx.commands["agency"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", {"mode": "regression", "feature": ""}),
        ("/audit_qa", {"mode": "regression", "feature": ""}),
        (
            "/audit_qa mode=smoke fitur=driver daily meal",
            {"mode": "smoke", "feature": "driver daily meal"},
        ),
        ("/qa_audit regression fitur=driver meal", {"mode": "regression", "feature": "driver meal"}),
        ("/audit_qa suite=visual fitur=MoboMap", {"mode": "visual", "feature": "MoboMap"}),
        ("/audit_qa help", {"mode": "help", "feature": "help"}),
        ("/audit_qa list fitur", {"mode": "list", "feature": "list"}),
        ("/audit_qa riwayat", {"mode": "history", "feature": "history"}),
        # An explicit feature keeps the turn on a real run mode: the help/list/history
        # shortcuts only apply when no feature was spelled out.
        (
            "/audit_qa mode=full fitur=driver help",
            {"mode": "full", "feature": "driver help"},
        ),
    ],
)
def test_parse_audit_qa_command(parser, raw, expected):
    assert parser.parse_audit_qa_command(raw) == expected


def test_legacy_parser_names_stay_exported(parser):
    """The core patch exported these from ``gateway.run``; callers/tests may still import them."""
    assert parser._parse_audit_qa_command is parser.parse_audit_qa_command
    assert parser._is_audit_qa_command is parser.is_audit_qa_command


@pytest.mark.parametrize(
    "raw",
    ["/audit_qa mode=smoke", "/audit-qa", "/qa_audit", "/QA_AUDIT fitur=x"],
)
def test_is_audit_qa_command_matches_every_spelling(parser, raw):
    assert parser.is_audit_qa_command(raw)


@pytest.mark.parametrize("raw", ["/help", "audit_qa", "/audit", "", None])
def test_is_audit_qa_command_ignores_other_input(parser, raw):
    assert not parser.is_audit_qa_command(raw)


def test_skill_bridge_resolves_skills_from_hermes_home(tmp_path, monkeypatch):
    """Regression guard: resolving against the skills home, not the checkout's bundled ``skills/``.

    The pre-plugin core patch imported ``skills.qa_automation`` relative to the checkout, which is
    exactly what broke on an installed hermes home. ``load_skill_module`` must prefer
    ``<HERMES_HOME>/skills``.
    """
    skill_dir = tmp_path / "skills" / "qa_skill_probe"
    skill_dir.mkdir(parents=True)
    (skill_dir / "__init__.py").write_text("ORIGIN = 'hermes-home'\n", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delitem(sys.modules, "qa_skill_probe", raising=False)

    from plugins.qa_audit import skill_bridge

    assert skill_bridge.skills_home() == tmp_path / "skills"
    assert skill_bridge.load_skill_module("qa_skill_probe").ORIGIN == "hermes-home"
    sys.modules.pop("qa_skill_probe", None)
