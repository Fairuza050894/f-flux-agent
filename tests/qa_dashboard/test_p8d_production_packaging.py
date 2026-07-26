from __future__ import annotations

from pathlib import Path

import pytest

from qa_dashboard.backend.frontend import (
    frontend_distribution_path,
    is_spa_route,
    production_frontend_enabled,
    validate_frontend_distribution,
)


def test_production_frontend_disabled_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "QA_DASHBOARD_SERVE_FRONTEND",
        raising=False,
    )

    assert (
        production_frontend_enabled()
        is False
    )


def test_production_frontend_can_be_enabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "QA_DASHBOARD_SERVE_FRONTEND",
        "true",
    )

    assert (
        production_frontend_enabled()
        is True
    )


def test_custom_frontend_distribution(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv(
        "QA_DASHBOARD_FRONTEND_DIST",
        str(tmp_path),
    )

    assert (
        frontend_distribution_path()
        == tmp_path.resolve()
    )


def test_distribution_requires_index_html(
    tmp_path,
):
    with pytest.raises(
        RuntimeError,
        match="index.html",
    ):
        validate_frontend_distribution(
            tmp_path,
        )


def test_valid_distribution_returns_index(
    tmp_path,
):
    index = tmp_path / "index.html"
    index.write_text(
        "<html></html>",
        encoding="utf-8",
    )

    assert (
        validate_frontend_distribution(
            tmp_path,
        )
        == index
    )


@pytest.mark.parametrize(
    "path",
    [
        "",
        "operations",
        "test-cycles/123",
        "test-assets/asset-1",
        "test-planning/plan-1",
        "projects",
        "environments",
        "integrations",
        "history",
        "reports",
    ],
)
def test_known_frontend_routes(
    path,
):
    assert is_spa_route(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "api/v1/health/ready",
        "auth/providers",
        "login",
        "unknown-api",
        "../secret",
    ],
)
def test_non_frontend_routes_are_not_spa(
    path,
):
    assert is_spa_route(path) is False
