#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify QA Dashboard production "
            "authentication end to end."
        ),
    )
    parser.add_argument(
        "--env-file",
        default=(
            "qa_dashboard/.env.production"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    from qa_dashboard.backend.environment import (
        load_dashboard_environment,
    )

    env_path = load_dashboard_environment(
        root=ROOT,
        env_file=args.env_file,
    )

    from qa_dashboard.backend.settings import (
        get_settings,
    )

    get_settings.cache_clear()
    settings = get_settings()

    if not settings.auth_required:
        raise RuntimeError(
            "Authentication is disabled in the "
            "selected production environment."
        )

    if not settings.auth_password:
        raise RuntimeError(
            "The local production auth doctor "
            "requires "
            "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD. "
            "A password hash alone cannot be tested "
            "without the original password."
        )

    from qa_dashboard.backend.app import app
    from qa_dashboard.backend.auth_diagnostics import (
        verify_password_authentication,
    )

    result = verify_password_authentication(
        app,
        username=settings.auth_username,
        password=settings.auth_password,
    )

    actor = (
        result.get("session", {})
        .get("actor", {})
    )

    print()
    print("=" * 72)
    print(
        "QA DASHBOARD AUTHENTICATION "
        "PREFLIGHT PASSED"
    )
    print("=" * 72)
    print(f"Environment : {env_path}")
    print(
        f"Provider    : "
        f"{result['provider']}"
    )
    print(
        f"Username    : "
        f"{settings.auth_username}"
    )
    print(
        f"Role        : "
        f"{actor.get('role', 'verified')}"
    )
    print(
        "Login       : HTTP "
        f"{result['login_status']}"
    )
    print(
        "Session     : HTTP "
        f"{result['session_status']}"
    )
    print(
        "Logout      : HTTP "
        f"{result['logout_status']}"
    )
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
