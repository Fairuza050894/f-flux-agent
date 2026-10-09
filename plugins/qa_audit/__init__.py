"""qa_audit plugin — the f-flux-agent fork's QA command surface, as a plugin.

Replaces the fork's core patches: ``/audit_qa`` (+ ``/qa_audit``) used to be hard-coded into
``gateway/run_inbound.py``/``gateway/run.py``, and ``/veriflow`` (+ ``/vf``), ``/autodev``
(+ ``/ad``) and ``/agency`` (+ ``/ag``) were ``CommandDef`` rows wired to ``HermesCLI`` methods plus
a now-unimplemented ``/check_landing_page`` row. All of them register here through the public
plugin API and work on both the CLI and the messaging gateway.

The QA skills are resolved from ``<HERMES_HOME>/skills`` at call time (see :mod:`.skill_bridge`) so
the plugin behaves the same in a fork checkout and in an installed hermes home.
"""

from __future__ import annotations

from . import audit, external

_AUDIT_ARGS_HINT = "[mode=<mode>] [fitur=<feature>] [url=<url>]"
_AUDIT_DESCRIPTION = (
    "Run the f-flux QA automation suite (Playwright) and route documentation/testing evidence "
    "to Telegram topics"
)


def register(ctx) -> None:
    """Register the fork QA commands on the plugin context."""
    # /audit-qa — the Telegram ``/audit_qa`` (underscores are normalized to hyphens by the gateway)
    # and its ``/qa_audit`` spelling. /check-landing-page keeps the removed ``check_landing_page``
    # CommandDef name alive; it runs the same landing-page audit entry point.
    ctx.register_command(
        "audit-qa", handler=audit.handle_audit_qa, description=_AUDIT_DESCRIPTION,
        args_hint=_AUDIT_ARGS_HINT,
    )
    ctx.register_command(
        "qa-audit", handler=audit.handle_audit_qa, description=_AUDIT_DESCRIPTION,
        args_hint=_AUDIT_ARGS_HINT,
    )
    ctx.register_command(
        "check-landing-page", handler=audit.handle_audit_qa,
        description="Run automated QA audit on a landing page", args_hint="<url>",
    )

    ctx.register_command(
        "veriflow", handler=external.handle_veriflow,
        description="Trigger Veriflow QA automation runs & get cinematic reports",
        args_hint="[run|status|report|wait|list|config] <args>",
    )
    ctx.register_command(
        "vf", handler=external.handle_veriflow,
        description="Alias for /veriflow", args_hint="<args>",
    )
    ctx.register_command(
        "autodev", handler=external.handle_autodev,
        description="Launch AutoDev Office projects (full SDLC: plan → code → QA → deploy)",
        args_hint="[create|status|logs|artifacts|url|approve|reject|list] <args>",
    )
    ctx.register_command(
        "ad", handler=external.handle_autodev,
        description="Alias for /autodev", args_hint="<args>",
    )
    ctx.register_command(
        "agency", handler=external.handle_agency,
        description="Browse & activate 200+ specialist AI personas from Agency Agents repo",
        args_hint="[list|use|install|update|workflow|run|clear] <args>",
    )
    ctx.register_command(
        "ag", handler=external.handle_agency,
        description="Alias for /agency", args_hint="<args>",
    )
