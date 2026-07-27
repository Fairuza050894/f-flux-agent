from __future__ import annotations

from pathlib import Path
from typing import Mapping
import os
import re

from dotenv import dotenv_values, load_dotenv


_ENV_KEY_PATTERN = re.compile(
    r"^\s*(?:export\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*="
)

_PROTECTED_PREFIXES = (
    "QA_DASHBOARD_",
    "HERMES_DASHBOARD_BASIC_AUTH_",
)

_PROTECTED_EXACT = {
    "APP_ENV",
    "QA_DEFAULT_URL",
}


def _resolve_path(
    root: Path,
    raw_path: str | Path,
) -> Path:
    path = Path(raw_path).expanduser()

    if not path.is_absolute():
        path = root / path

    return path.resolve()


def _duplicate_keys(
    path: Path,
) -> tuple[str, ...]:
    counts: dict[str, int] = {}

    for line in path.read_text(
        encoding="utf-8",
    ).splitlines():
        match = _ENV_KEY_PATTERN.match(line)

        if match is None:
            continue

        key = match.group(1)
        counts[key] = counts.get(key, 0) + 1

    return tuple(
        sorted(
            key
            for key, count in counts.items()
            if count > 1
        )
    )


def _clear_protected_environment() -> None:
    for key in tuple(os.environ):
        if (
            key in _PROTECTED_EXACT
            or key.startswith(
                _PROTECTED_PREFIXES
            )
        ):
            os.environ.pop(key, None)


def _apply_values(
    values: Mapping[str, object],
) -> None:
    for key, value in values.items():
        if value is None:
            os.environ.pop(key, None)
            continue

        os.environ[key] = str(value)


def load_dashboard_environment(
    *,
    root: Path | None = None,
    env_file: str | Path | None = None,
) -> Path | None:
    """Load one deterministic QA Dashboard environment.

    When QA_DASHBOARD_ENV_FILE (or ``env_file``) is set, that
    file is authoritative for dashboard and basic-auth keys.
    The legacy skills/qa_automation/.env file is not allowed to
    overwrite it later during settings bootstrap.
    """

    project_root = (
        root.resolve()
        if root is not None
        else Path(__file__).resolve().parents[2]
    )

    selected = str(
        env_file
        or os.environ.get(
            "QA_DASHBOARD_ENV_FILE",
            "",
        )
    ).strip()

    if selected:
        path = _resolve_path(
            project_root,
            selected,
        )

        if not path.is_file():
            raise RuntimeError(
                "QA Dashboard environment file "
                f"was not found: {path}"
            )

        duplicates = _duplicate_keys(path)

        if duplicates:
            raise RuntimeError(
                "Duplicate environment keys are "
                "not allowed in the selected QA "
                "Dashboard environment file: "
                + ", ".join(duplicates)
            )

        values = dotenv_values(path)

        _clear_protected_environment()
        _apply_values(values)

        os.environ[
            "QA_DASHBOARD_ENV_FILE"
        ] = str(path)

        return path

    load_dotenv(
        project_root / ".env",
        override=False,
    )
    load_dotenv(
        (
            project_root
            / "skills"
            / "qa_automation"
            / ".env"
        ),
        override=False,
    )

    return None
