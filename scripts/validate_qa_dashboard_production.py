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
            "Validate Hermes QA Dashboard "
            "production configuration and auth."
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
    settings.validate()

    from qa_dashboard.backend.database import (
        database_health,
    )

    database = database_health()

    if database.get("status") != "ready":
        raise RuntimeError(
            "Database readiness failed: "
            f"{database}"
        )

    from qa_dashboard.backend.app import app
    from qa_dashboard.backend.auth_diagnostics import (
        verify_password_authentication,
    )

    if settings.auth_required:
        if not settings.auth_password:
            raise RuntimeError(
                "Production validation requires "
                "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD "
                "in the local environment file."
            )

        auth_result = (
            verify_password_authentication(
                app,
                username=
                    settings.auth_username,
                password=
                    settings.auth_password,
            )
        )
    else:
        auth_result = {
            "login_status": "disabled",
            "session_status": "disabled",
            "logout_status": "disabled",
        }

    print()
    print("=" * 72)
    print(
        "QA DASHBOARD PRODUCTION "
        "VALIDATION PASSED"
    )
    print("=" * 72)
    print(f"Environment : {env_path}")
    print(
        f"App mode    : "
        f"{settings.app_environment}"
    )
    print(
        f"Database    : "
        f"{database.get('status')}"
    )
    print(
        f"Auth        : "
        f"{'required' if settings.auth_required else 'disabled'}"
    )
    print(
        f"Login       : "
        f"{auth_result['login_status']}"
    )
    print(
        f"Session     : "
        f"{auth_result['session_status']}"
    )
    print(
        f"Logout      : "
        f"{auth_result['logout_status']}"
    )
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
