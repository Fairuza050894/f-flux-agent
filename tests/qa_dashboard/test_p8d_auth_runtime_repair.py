from __future__ import annotations

from pathlib import Path

import pytest

from qa_dashboard.backend.environment import (
    load_dashboard_environment,
)


def test_selected_environment_rejects_duplicates(
    tmp_path,
):
    env_path = tmp_path / ".env.production"
    env_path.write_text(
        "APP_ENV=production\n"
        "APP_ENV=development\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="Duplicate environment keys",
    ):
        load_dashboard_environment(
            root=tmp_path,
            env_file=env_path,
        )


def test_selected_environment_overrides_stale_auth(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "HERMES_DASHBOARD_BASIC_AUTH_USERNAME",
        "stale-user",
    )

    env_path = tmp_path / ".env.production"
    env_path.write_text(
        "APP_ENV=production\n"
        "HERMES_DASHBOARD_BASIC_AUTH_USERNAME="
        "canonical-user\n",
        encoding="utf-8",
    )

    selected = load_dashboard_environment(
        root=tmp_path,
        env_file=env_path,
    )

    assert selected == env_path.resolve()

    import os

    assert (
        os.environ[
            "HERMES_DASHBOARD_BASIC_AUTH_USERNAME"
        ]
        == "canonical-user"
    )


def test_registry_exposes_atomic_provider_replace():
    source = (
        Path(
            "hermes_cli/dashboard_auth/"
            "registry.py"
        )
        .read_text(encoding="utf-8")
    )
    exports = (
        Path(
            "hermes_cli/dashboard_auth/"
            "__init__.py"
        )
        .read_text(encoding="utf-8")
    )

    assert "def replace_provider(" in source
    assert "replace_provider" in exports


def test_security_replaces_stale_basic_provider():
    source = (
        Path(
            "qa_dashboard/backend/security.py"
        )
        .read_text(encoding="utf-8")
    )

    assert "replace_provider(provider)" in source
    assert "_reset_password_rate_limit" in source


def test_production_runner_has_auth_preflight():
    source = (
        Path(
            "scripts/qa_dashboard_production.py"
        )
        .read_text(encoding="utf-8")
    )

    assert "verify_password_authentication" in source
    assert "reload=False" in source
    assert "QA_DASHBOARD_ENV_FILE" not in source
