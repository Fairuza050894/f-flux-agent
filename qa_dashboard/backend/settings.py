from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Tuple
import os

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
QA_AUTOMATION_ENV_PATH = (
    ROOT
    / "skills"
    / "qa_automation"
    / ".env"
)

load_dotenv(
    ROOT / ".env",
    override=False,
)
load_dotenv(
    QA_AUTOMATION_ENV_PATH,
    override=True,
)


def _environment_value(
    name: str,
    fallback: str = "",
) -> str:
    value = os.getenv(name)

    if value is None:
        return fallback

    return str(value).strip()


def _boolean_value(
    name: str,
    fallback: bool = False,
) -> bool:
    value = _environment_value(name)

    if not value:
        return fallback

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _frontend_origins() -> Tuple[str, ...]:
    raw_value = _environment_value(
        "QA_DASHBOARD_FRONTEND_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
    )

    origins = tuple(
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    )

    return origins or (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


@dataclass(
    frozen=True,
)
class DashboardSettings:
    app_environment: str
    database_url: str
    default_base_url: str
    frontend_origins: Tuple[str, ...]
    strict_configuration: bool
    sync_enabled: bool
    workspace_id: str

    @property
    def database_driver(
        self,
    ) -> str:
        return self.database_url.split(
            ":",
            1,
        )[0].lower()

    @property
    def is_production(
        self,
    ) -> bool:
        return self.app_environment in {
            "production",
            "prod",
        }

    def validate(
        self,
    ) -> None:
        if not self.workspace_id:
            raise RuntimeError(
                "QA_DASHBOARD_WORKSPACE_ID "
                "must not be empty."
            )

        if self.database_driver != "sqlite":
            raise RuntimeError(
                "P8-A currently supports SQLite "
                "through QA_DASHBOARD_DATABASE_URL. "
                "The persistence adapter boundary is "
                "ready for a PostgreSQL adapter in a "
                "later hardening checkpoint."
            )

        if (
            self.is_production
            and "*" in self.frontend_origins
        ):
            raise RuntimeError(
                "Production CORS origins must be "
                "explicit. Wildcard origins are not "
                "allowed."
            )

        if (
            self.strict_configuration
            and not self.frontend_origins
        ):
            raise RuntimeError(
                "QA_DASHBOARD_FRONTEND_ORIGINS "
                "must be configured."
            )

    def public_summary(
        self,
    ) -> dict:
        return {
            "app_environment":
                self.app_environment,
            "database_driver":
                self.database_driver,
            "frontend_origins":
                list(self.frontend_origins),
            "strict_configuration":
                self.strict_configuration,
            "sync_enabled":
                self.sync_enabled,
            "workspace_id":
                self.workspace_id,
        }


@lru_cache(
    maxsize=1,
)
def get_settings() -> DashboardSettings:
    settings = DashboardSettings(
        app_environment=
            _environment_value(
                "APP_ENV",
                "development",
            ).lower(),
        database_url=
            _environment_value(
                "QA_DASHBOARD_DATABASE_URL",
                (
                    "sqlite:///"
                    "skills/qa_automation/"
                    "artifacts/runtime/"
                    "qa_dashboard.db"
                ),
            ),
        default_base_url=
            _environment_value(
                "QA_DEFAULT_URL",
                (
                    "https://mobospace-sandbox."
                    "pancaran-group.co.id"
                ),
            ),
        frontend_origins=
            _frontend_origins(),
        strict_configuration=
            _boolean_value(
                "QA_DASHBOARD_STRICT_CONFIG",
                False,
            ),
        sync_enabled=
            _boolean_value(
                "QA_DASHBOARD_SYNC_ENABLED",
                True,
            ),
        workspace_id=
            _environment_value(
                "QA_DASHBOARD_WORKSPACE_ID",
                "default",
            ),
    )

    settings.validate()
    return settings
