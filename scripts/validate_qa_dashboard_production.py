#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_ENV_FILE = (
    ROOT
    / "qa_dashboard"
    / ".env.production"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Hermes QA Dashboard "
            "production configuration and "
            "frontend packaging."
        )
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_file = (
        args.env_file
        .expanduser()
        .resolve()
    )

    if not env_file.is_file():
        raise SystemExit(
            f"Environment file not found: "
            f"{env_file}"
        )

    os.environ[
        "QA_DASHBOARD_ENV_FILE"
    ] = str(env_file)
    os.environ.setdefault(
        "QA_DASHBOARD_SERVE_FRONTEND",
        "true",
    )

    from qa_dashboard.backend.database import (
        database_health,
    )
    from qa_dashboard.backend.frontend import (
        frontend_distribution_path,
        validate_frontend_distribution,
    )
    from qa_dashboard.backend.settings import (
        get_settings,
    )

    settings = get_settings()

    if not settings.is_production:
        raise SystemExit(
            "APP_ENV must be production "
            "or prod."
        )

    distribution = (
        frontend_distribution_path()
    )
    index_path = (
        validate_frontend_distribution(
            distribution,
        )
    )
    database = database_health()

    if database.get("status") != "ready":
        raise SystemExit(
            "Database readiness validation "
            f"failed: {database}"
        )

    print(
        "QA DASHBOARD PRODUCTION "
        "VALIDATION PASSED"
    )
    print(
        f"Environment: "
        f"{settings.app_environment}"
    )
    print(
        f"Frontend origin(s): "
        f"{', '.join(settings.frontend_origins)}"
    )
    print(f"Frontend index: {index_path}")
    print(
        f"Database status: "
        f"{database.get('status')}"
    )
    print(
        f"Authentication configured: "
        f"{settings.auth_configured}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
