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
QA_DASHBOARD_ENV_PATH = (
    ROOT
    / "qa_dashboard"
    / ".env"
)
CUSTOM_ENV_PATH = str(
    os.getenv(
        "QA_DASHBOARD_ENV_FILE",
        "",
    )
).strip()

if CUSTOM_ENV_PATH:
    load_dotenv(
        Path(
            CUSTOM_ENV_PATH,
        ).expanduser(),
        override=True,
    )
else:
    load_dotenv(
        ROOT / ".env",
        override=False,
    )
    load_dotenv(
        QA_DASHBOARD_ENV_PATH,
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


def _integer_value(
    name: str,
    fallback: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    value = _environment_value(name)

    try:
        parsed = (
            int(value)
            if value
            else int(fallback)
        )
    except ValueError:
        parsed = int(fallback)

    return max(
        minimum,
        min(
            maximum,
            parsed,
        ),
    )


def _csv_values(
    name: str,
    fallback: str = "",
) -> Tuple[str, ...]:
    raw_value = _environment_value(
        name,
        fallback,
    )

    return tuple(
        item.strip().lower()
        for item in raw_value.split(",")
        if item.strip()
    )


def _frontend_origins() -> Tuple[str, ...]:
    origins = _csv_values(
        "QA_DASHBOARD_FRONTEND_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
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

    auth_required: bool
    auth_username: str
    auth_password_hash: str
    auth_password: str
    auth_secret: str
    auth_ttl_seconds: int
    basic_auth_role: str

    admin_users: Tuple[str, ...]
    qa_lead_users: Tuple[str, ...]
    tester_users: Tuple[str, ...]
    viewer_users: Tuple[str, ...]

    allow_private_targets: bool
    max_request_bytes: int
    write_rate_limit_per_minute: int

    audit_max_events: int
    stale_execution_seconds: int
    readiness_require_telegram: bool
    operations_poll_seconds: int

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

    @property
    def auth_configured(
        self,
    ) -> bool:
        return bool(
            self.auth_username
            and (
                self.auth_password_hash
                or self.auth_password
            )
        )

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
                "P8 currently supports SQLite "
                "through QA_DASHBOARD_DATABASE_URL. "
                "The persistence adapter boundary "
                "remains ready for PostgreSQL."
            )

        if (
            self.is_production
            and "*" in self.frontend_origins
        ):
            raise RuntimeError(
                "Production CORS origins must be "
                "explicit. Wildcard origins are "
                "not allowed."
            )

        if (
            self.strict_configuration
            and not self.frontend_origins
        ):
            raise RuntimeError(
                "QA_DASHBOARD_FRONTEND_ORIGINS "
                "must be configured."
            )

        if (
            self.is_production
            and not self.auth_required
        ):
            raise RuntimeError(
                "Production requires "
                "QA_DASHBOARD_AUTH_REQUIRED=true."
            )

        if (
            self.auth_required
            and not self.auth_configured
        ):
            raise RuntimeError(
                "Authentication is enabled but "
                "basic-auth credentials are "
                "missing. Configure "
                "HERMES_DASHBOARD_BASIC_AUTH_"
                "USERNAME and either PASSWORD_HASH "
                "or PASSWORD."
            )

        if (
            self.is_production
            and self.auth_required
            and len(
                self.auth_secret.encode(
                    "utf-8",
                )
            ) < 16
        ):
            raise RuntimeError(
                "Production requires a stable "
                "HERMES_DASHBOARD_BASIC_AUTH_SECRET "
                "with at least 16 bytes."
            )

        if self.basic_auth_role not in {
            "admin",
            "qa_lead",
            "tester",
            "viewer",
        }:
            raise RuntimeError(
                "QA_DASHBOARD_BASIC_AUTH_ROLE "
                "must be admin, qa_lead, tester, "
                "or viewer."
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
            "auth_required":
                self.auth_required,
            "auth_configured":
                self.auth_configured,
            "auth_provider":
                (
                    "basic"
                    if self.auth_configured
                    else None
                ),
            "allow_private_targets":
                self.allow_private_targets,
            "max_request_bytes":
                self.max_request_bytes,
            "write_rate_limit_per_minute":
                self.write_rate_limit_per_minute,
            "audit_max_events":
                self.audit_max_events,
            "stale_execution_seconds":
                self.stale_execution_seconds,
            "readiness_require_telegram":
                self.readiness_require_telegram,
            "operations_poll_seconds":
                self.operations_poll_seconds,
        }


@lru_cache(
    maxsize=1,
)
def get_settings() -> DashboardSettings:
    app_environment = _environment_value(
        "APP_ENV",
        "development",
    ).lower()

    is_production = (
        app_environment
        in {
            "production",
            "prod",
        }
    )

    auth_username = _environment_value(
        "HERMES_DASHBOARD_BASIC_AUTH_USERNAME",
        "",
    )

    settings = DashboardSettings(
        app_environment=
            app_environment,
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

        auth_required=
            _boolean_value(
                "QA_DASHBOARD_AUTH_REQUIRED",
                is_production,
            ),
        auth_username=
            auth_username,
        auth_password_hash=
            _environment_value(
                "HERMES_DASHBOARD_BASIC_AUTH_"
                "PASSWORD_HASH",
                "",
            ),
        auth_password=
            _environment_value(
                "HERMES_DASHBOARD_BASIC_AUTH_"
                "PASSWORD",
                "",
            ),
        auth_secret=
            _environment_value(
                "HERMES_DASHBOARD_BASIC_AUTH_SECRET",
                "",
            ),
        auth_ttl_seconds=
            _integer_value(
                "HERMES_DASHBOARD_BASIC_AUTH_"
                "TTL_SECONDS",
                43200,
                minimum=300,
                maximum=2592000,
            ),
        basic_auth_role=
            _environment_value(
                "QA_DASHBOARD_BASIC_AUTH_ROLE",
                "admin",
            ).lower(),

        admin_users=
            _csv_values(
                "QA_DASHBOARD_ADMIN_USERS",
                auth_username,
            ),
        qa_lead_users=
            _csv_values(
                "QA_DASHBOARD_QA_LEAD_USERS",
            ),
        tester_users=
            _csv_values(
                "QA_DASHBOARD_TESTER_USERS",
            ),
        viewer_users=
            _csv_values(
                "QA_DASHBOARD_VIEWER_USERS",
            ),

        allow_private_targets=
            _boolean_value(
                "QA_DASHBOARD_ALLOW_PRIVATE_TARGETS",
                False,
            ),
        max_request_bytes=
            _integer_value(
                "QA_DASHBOARD_MAX_REQUEST_BYTES",
                15728640,
                minimum=1024,
                maximum=104857600,
            ),
        write_rate_limit_per_minute=
            _integer_value(
                "QA_DASHBOARD_WRITE_RATE_LIMIT_"
                "PER_MINUTE",
                120,
                minimum=5,
                maximum=10000,
            ),

        audit_max_events=
            _integer_value(
                "QA_DASHBOARD_AUDIT_MAX_EVENTS",
                5000,
                minimum=100,
                maximum=20000,
            ),
        stale_execution_seconds=
            _integer_value(
                "QA_DASHBOARD_STALE_EXECUTION_"
                "SECONDS",
                1800,
                minimum=60,
                maximum=604800,
            ),
        readiness_require_telegram=
            _boolean_value(
                "QA_DASHBOARD_READINESS_REQUIRE_"
                "TELEGRAM",
                False,
            ),
        operations_poll_seconds=
            _integer_value(
                "QA_DASHBOARD_OPERATIONS_POLL_"
                "SECONDS",
                15,
                minimum=5,
                maximum=300,
            ),
    )

    settings.validate()
    return settings
