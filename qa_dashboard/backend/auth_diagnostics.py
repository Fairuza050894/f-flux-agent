from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient


class AuthenticationDiagnosticError(
    RuntimeError,
):
    pass


def verify_password_authentication(
    app: FastAPI,
    *,
    username: str,
    password: str,
) -> dict[str, Any]:
    """Exercise the real login, session, and logout routes."""

    if not username or not password:
        raise AuthenticationDiagnosticError(
            "A username and plaintext password "
            "are required for the authentication "
            "preflight."
        )

    from hermes_cli.dashboard_auth.routes import (
        _reset_password_rate_limit,
    )

    _reset_password_rate_limit()

    with TestClient(
        app,
        base_url="http://127.0.0.1:8765",
    ) as client:
        providers_response = client.get(
            "/api/auth/providers",
        )

        if providers_response.status_code != 200:
            raise AuthenticationDiagnosticError(
                "Provider discovery failed with "
                f"HTTP {providers_response.status_code}: "
                f"{providers_response.text}"
            )

        providers_payload = (
            providers_response.json()
        )
        provider_names = {
            str(provider.get("name", ""))
            for provider in providers_payload.get(
                "providers",
                [],
            )
        }

        if "basic" not in provider_names:
            raise AuthenticationDiagnosticError(
                "The basic authentication provider "
                "is not registered."
            )

        login_response = client.post(
            "/auth/password-login",
            json={
                "provider": "basic",
                "username": username,
                "password": password,
                "next": "/",
            },
        )

        if login_response.status_code != 200:
            raise AuthenticationDiagnosticError(
                "Password login failed with "
                f"HTTP {login_response.status_code}: "
                f"{login_response.text}"
            )

        session_response = client.get(
            "/api/v1/security/session",
        )

        if session_response.status_code != 200:
            raise AuthenticationDiagnosticError(
                "The login route returned success, "
                "but the authenticated session "
                "probe failed with "
                f"HTTP {session_response.status_code}: "
                f"{session_response.text}"
            )

        session_payload = (
            session_response.json()
        )

        logout_response = client.post(
            "/auth/logout",
            follow_redirects=False,
        )

        if logout_response.status_code not in {
            302,
            303,
        }:
            raise AuthenticationDiagnosticError(
                "Logout verification failed with "
                f"HTTP {logout_response.status_code}: "
                f"{logout_response.text}"
            )

    return {
        "provider": "basic",
        "username": username,
        "session": session_payload,
        "login_status": 200,
        "session_status": 200,
        "logout_status":
            logout_response.status_code,
    }
