from __future__ import annotations

import pytest

from qa_dashboard.backend.settings import (
    get_settings,
)


BASE_PRODUCTION_ENV = {
    "APP_ENV": "production",
    "QA_DASHBOARD_DATABASE_URL":
        "sqlite:///tmp/p8d-quality-gate.db",
    "QA_DASHBOARD_FRONTEND_ORIGINS":
        "https://qa.example.test",
    "QA_DASHBOARD_WORKSPACE_ID": "ci",
    "QA_DASHBOARD_SYNC_ENABLED": "true",
    "QA_DASHBOARD_STRICT_CONFIG": "true",
    "QA_DASHBOARD_AUTH_REQUIRED": "true",
    "HERMES_DASHBOARD_BASIC_AUTH_USERNAME":
        "ci-admin",
    "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH":
        "",
    "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD":
        "ci-only-password",
    "HERMES_DASHBOARD_BASIC_AUTH_SECRET":
        "0123456789abcdef0123456789abcdef",
    "HERMES_DASHBOARD_BASIC_AUTH_TTL_SECONDS":
        "3600",
    "QA_DASHBOARD_BASIC_AUTH_ROLE": "admin",
}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def configure(
    monkeypatch,
    **overrides,
):
    values = {
        **BASE_PRODUCTION_ENV,
        **overrides,
    }

    for key, value in values.items():
        monkeypatch.setenv(
            key,
            str(value),
        )

    get_settings.cache_clear()
    return get_settings()


def test_valid_production_configuration(
    monkeypatch,
):
    settings = configure(monkeypatch)

    assert settings.is_production is True
    assert settings.auth_required is True
    assert settings.auth_configured is True
    assert settings.frontend_origins == (
        "https://qa.example.test",
    )


def test_production_requires_authentication(
    monkeypatch,
):
    with pytest.raises(
        RuntimeError,
        match="Production requires",
    ):
        configure(
            monkeypatch,
            QA_DASHBOARD_AUTH_REQUIRED="false",
        )


def test_production_rejects_wildcard_cors(
    monkeypatch,
):
    with pytest.raises(
        RuntimeError,
        match="Wildcard origins",
    ):
        configure(
            monkeypatch,
            QA_DASHBOARD_FRONTEND_ORIGINS="*",
        )


def test_production_requires_stable_auth_secret(
    monkeypatch,
):
    with pytest.raises(
        RuntimeError,
        match="at least 16 bytes",
    ):
        configure(
            monkeypatch,
            HERMES_DASHBOARD_BASIC_AUTH_SECRET="short",
        )


def test_public_summary_does_not_expose_secrets(
    monkeypatch,
):
    settings = configure(monkeypatch)
    summary = settings.public_summary()

    serialized = repr(summary).lower()

    assert "ci-only-password" not in serialized
    assert (
        "0123456789abcdef0123456789abcdef"
        not in serialized
    )
    assert "auth_password" not in summary
    assert "auth_secret" not in summary
