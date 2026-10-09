"""Locate the fork QA skills at runtime.

The QA skills (``qa_automation``, ``veriflow_trigger``, ``autodev_launcher``, ``agency``) live under
``<HERMES_HOME>/skills`` in a live install — the ``skills/`` directory next to a checkout only
carries the upstream bundled skills there. Resolving through ``get_hermes_home()`` keeps this plugin
working both from the fork checkout and from an installed hermes (the fork's own core patch imported
``skills.qa_automation`` relative to the checkout, which is exactly what broke on installed homes).
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


def skills_home() -> Path:
    """The active profile's skills directory (``<HERMES_HOME>/skills``)."""
    return get_hermes_home() / "skills"


def load_skill_module(name: str) -> Any:
    """Import skill package *name* from the Hermes skills home, preferring it over the checkout.

    The skills home directory is prepended to ``sys.path`` so a skill that uses sibling absolute
    imports resolves its own package tree. A developer running from a fork checkout that has not
    installed the skills into ``$HERMES_HOME`` yet falls back to the bundled ``skills.<name>``
    package shipped in that checkout.
    """
    cached = sys.modules.get(name)
    if cached is not None:
        return cached

    home_dir = skills_home() / name
    if home_dir.is_dir():
        entry = str(home_dir.parent)
        if entry not in sys.path:
            sys.path.insert(0, entry)
        return importlib.import_module(name)

    try:
        return importlib.import_module(f"skills.{name}")
    except ImportError as exc:
        raise ImportError(
            f"QA skill '{name}' is not installed: expected {home_dir} "
            f"(copy the fork skills into {skills_home()} or run from the fork checkout)"
        ) from exc
