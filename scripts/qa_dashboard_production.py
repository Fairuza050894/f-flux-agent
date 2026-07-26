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
            "Run Hermes QA Dashboard in "
            "single-origin production mode."
        )
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help=(
            "Production environment file. "
            "Defaults to qa_dashboard/"
            ".env.production."
        ),
    )
    parser.add_argument(
        "--host",
        default=None,
        help=(
            "Bind host. Defaults to "
            "QA_DASHBOARD_HOST or 127.0.0.1."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=(
            "Bind port. Defaults to "
            "QA_DASHBOARD_PORT or 8765."
        ),
    )
    return parser.parse_args()


def load_environment(
    env_file: Path,
) -> Path:
    resolved = env_file.expanduser().resolve()

    if not resolved.is_file():
        raise SystemExit(
            "Production environment file "
            f"was not found: {resolved}. "
            "Copy qa_dashboard/"
            ".env.production.example to "
            "qa_dashboard/.env.production "
            "and configure it."
        )

    os.environ[
        "QA_DASHBOARD_ENV_FILE"
    ] = str(resolved)
    os.environ.setdefault(
        "QA_DASHBOARD_SERVE_FRONTEND",
        "true",
    )
    return resolved


def main() -> int:
    args = parse_args()
    env_file = load_environment(
        args.env_file,
    )

    # Import only after QA_DASHBOARD_ENV_FILE
    # is selected so settings cannot be
    # overridden by the QA automation .env.
    from qa_dashboard.backend.frontend import (
        frontend_distribution_path,
        validate_frontend_distribution,
    )
    from qa_dashboard.backend.settings import (
        get_settings,
    )

    settings = get_settings()
    distribution = (
        frontend_distribution_path()
    )
    validate_frontend_distribution(
        distribution,
    )

    if not settings.is_production:
        raise SystemExit(
            "APP_ENV must be production "
            "or prod."
        )

    if not settings.auth_required:
        raise SystemExit(
            "Authentication must be enabled "
            "for production."
        )

    host = (
        args.host
        or os.getenv(
            "QA_DASHBOARD_HOST",
            "127.0.0.1",
        )
    )
    port = (
        args.port
        or int(
            os.getenv(
                "QA_DASHBOARD_PORT",
                "8765",
            )
        )
    )
    forwarded_allow_ips = os.getenv(
        "QA_DASHBOARD_FORWARDED_ALLOW_IPS",
        "127.0.0.1",
    )

    print(
        "Hermes QA Dashboard production runtime"
    )
    print(f"Environment file: {env_file}")
    print(f"Frontend dist: {distribution}")
    print(f"Bind address: {host}:{port}")
    print(
        "Health: "
        f"http://{host}:{port}"
        "/api/v1/health/ready"
    )

    import uvicorn

    uvicorn.run(
        "qa_dashboard.backend.app:app",
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips=
            forwarded_allow_ips,
        reload=False,
        access_log=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
