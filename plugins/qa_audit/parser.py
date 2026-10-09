"""Parser for the fork's ``/audit_qa`` command, moved out of ``gateway/run.py``.

``parse_audit_qa_command`` is the single-pass merge of the three ``_parse_audit_qa_command``
definitions the fork installed in core: the base ``mode=``/``fitur=`` parser plus the two
late patches that recognise the ``help``/``list`` and ``history`` argument texts. Behaviour is
kept byte-for-byte compatible with the core version it replaces.
"""

from __future__ import annotations

_RUN_MODES = frozenset(
    {"smoke", "regression", "full", "visual", "cross_feature", "negative", "e2e"}
)
_HELP_ARG_TEXTS = frozenset({"help", "bantuan", "cara pakai", "?"})
_LIST_ARG_TEXTS = frozenset(
    {"list", "features", "feature list", "daftar", "daftar fitur", "list fitur"}
)
_HISTORY_ARG_TEXTS = frozenset(
    {"history", "qa history", "run history", "riwayat", "histori", "riwayat qa"}
)
_EXPLICIT_FEATURE_MARKERS = ("fitur=", "feature=", "module=", "module_name=")


def parse_audit_qa_command(text: str) -> dict:
    """Parse a ``/audit_qa`` (or ``/qa_audit``) invocation into ``{"mode": ..., "feature": ...}``.

    Examples::

        /audit_qa mode=regression fitur=driver daily meal
        /audit_qa regression fitur=driver meal
        /qa_audit mode=smoke fitur=driver daily meal
    """

    raw_text = (text or "").strip()
    parts = raw_text.split()

    result = {"mode": "regression", "feature": ""}

    if not parts:
        return result

    # Remove command token
    args = parts[1:]

    collecting_feature = False
    feature_parts: list[str] = []

    for arg in args:
        normalized = arg.strip()

        if not normalized:
            continue

        lower = normalized.lower()

        if lower.startswith("mode="):
            result["mode"] = normalized.split("=", 1)[1].strip().lower()
            collecting_feature = False
            continue

        if lower.startswith("suite="):
            result["mode"] = normalized.split("=", 1)[1].strip().lower()
            collecting_feature = False
            continue

        if lower.startswith("fitur=") or lower.startswith("feature="):
            feature_value = normalized.split("=", 1)[1].strip()
            if feature_value:
                feature_parts.append(feature_value)
            collecting_feature = True
            continue

        # Support: /audit_qa regression
        if lower in _RUN_MODES:
            result["mode"] = lower
            collecting_feature = False
            continue

        # Continue feature phrase after fitur=
        if collecting_feature:
            feature_parts.append(normalized)

    result["feature"] = " ".join(feature_parts).strip()

    # ``help`` / ``list`` / ``history`` are only recognised when the caller did not spell out a
    # feature (mirrors the two patches the fork appended to gateway/run.py).
    lowered = raw_text.lower().replace("_", "-")
    tokens = lowered.split()
    arg_tokens = tokens[1:] if tokens and tokens[0].startswith("/") else tokens
    arg_text = " ".join(arg_tokens).strip()

    has_explicit_feature = any(marker in lowered for marker in _EXPLICIT_FEATURE_MARKERS)

    if not has_explicit_feature:
        if arg_text in _HELP_ARG_TEXTS:
            result["mode"] = "help"
            result["feature"] = "help"
        elif arg_text in _LIST_ARG_TEXTS:
            result["mode"] = "list"
            result["feature"] = "list"
        elif arg_text in _HISTORY_ARG_TEXTS:
            result["mode"] = "history"
            result["feature"] = "history"

    return result


def is_audit_qa_command(text: str) -> bool:
    """Whether *text* addresses the fork QA command under any of its spellings."""
    raw_text = (text or "").strip().lower()
    return (
        raw_text.startswith("/audit_qa")
        or raw_text.startswith("/audit-qa")
        or raw_text.startswith("/qa_audit")
        or raw_text.startswith("/qa-audit")
    )


# Names the core patch exported from ``gateway.run``; kept so callers/tests written against the
# pre-plugin layout keep resolving.
_parse_audit_qa_command = parse_audit_qa_command
_is_audit_qa_command = is_audit_qa_command

__all__ = [
    "_is_audit_qa_command",
    "_parse_audit_qa_command",
    "is_audit_qa_command",
    "parse_audit_qa_command",
]
