from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


ROOT: Final[Path] = (
    Path(__file__).resolve().parents[2]
)
DEFAULT_FRONTEND_DIST: Final[Path] = (
    ROOT
    / "qa_dashboard"
    / "frontend_v3"
    / "dist"
)

SPA_ROUTE_ROOTS: Final[frozenset[str]] = (
    frozenset(
        {
            "",
            "test-cycles",
            "test-assets",
            "test-planning",
            "history",
            "reports",
            "projects",
            "environments",
            "integrations",
            "operations",
    "account",
        }
    )
)


def _boolean_environment(
    name: str,
    fallback: bool = False,
) -> bool:
    value = str(
        os.getenv(
            name,
            "",
        )
    ).strip()

    if not value:
        return fallback

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def production_frontend_enabled() -> bool:
    return _boolean_environment(
        "QA_DASHBOARD_SERVE_FRONTEND",
        False,
    )


def frontend_distribution_path() -> Path:
    configured = str(
        os.getenv(
            "QA_DASHBOARD_FRONTEND_DIST",
            "",
        )
    ).strip()

    if not configured:
        return DEFAULT_FRONTEND_DIST

    path = Path(
        configured,
    ).expanduser()

    if not path.is_absolute():
        path = ROOT / path

    return path.resolve()


def validate_frontend_distribution(
    distribution: Path,
) -> Path:
    resolved = distribution.resolve()
    index_path = resolved / "index.html"

    if not resolved.is_dir():
        raise RuntimeError(
            "QA Dashboard frontend distribution "
            f"directory does not exist: {resolved}. "
            "Run npm run build in "
            "qa_dashboard/frontend_v3."
        )

    if not index_path.is_file():
        raise RuntimeError(
            "QA Dashboard frontend index.html "
            f"was not found: {index_path}."
        )

    return index_path


def is_spa_route(
    full_path: str,
) -> bool:
    normalized = str(
        full_path or "",
    ).strip("/")

    if not normalized:
        return True

    root_segment = normalized.split(
        "/",
        1,
    )[0]

    return root_segment in SPA_ROUTE_ROOTS


def _index_response(
    index_path: Path,
) -> FileResponse:
    return FileResponse(
        index_path,
        media_type="text/html",
        headers={
            "Cache-Control":
                "no-store, no-cache, "
                "must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def install_production_frontend(
    app: FastAPI,
) -> bool:
    if not production_frontend_enabled():
        return False

    distribution = (
        frontend_distribution_path()
    )
    index_path = (
        validate_frontend_distribution(
            distribution,
        )
    )
    assets_path = distribution / "assets"

    if assets_path.is_dir():
        app.mount(
            "/assets",
            StaticFiles(
                directory=assets_path,
            ),
            name="qa-dashboard-assets",
        )

    @app.get(
        "/",
        include_in_schema=False,
    )
    async def qa_dashboard_index():
        return _index_response(
            index_path,
        )

    @app.get(
        "/{full_path:path}",
        include_in_schema=False,
    )
    async def qa_dashboard_spa(
        full_path: str,
    ):
        if not is_spa_route(
            full_path,
        ):
            raise HTTPException(
                status_code=404,
                detail="Not found",
            )

        candidate = (
            distribution
            / full_path
        ).resolve()

        try:
            candidate.relative_to(
                distribution,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=404,
                detail="Not found",
            ) from error

        if candidate.is_file():
            return FileResponse(
                candidate,
            )

        return _index_response(
            index_path,
        )

    return True
