from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional
import json
import sqlite3

from qa_dashboard.backend.settings import (
    ROOT,
    get_settings,
)


DATABASE_LOCK = RLock()
SCHEMA_VERSION = 1


class RevisionConflict(
    RuntimeError,
):
    def __init__(
        self,
        current_revision: int,
    ) -> None:
        super().__init__(
            "Stored document revision changed."
        )
        self.current_revision = (
            current_revision
        )


def utc_now() -> str:
    return datetime.now(
        timezone.utc,
    ).isoformat()


def _sqlite_path() -> Path:
    database_url = (
        get_settings().database_url
    )
    prefix = "sqlite:///"

    if not database_url.startswith(
        prefix
    ):
        raise RuntimeError(
            "Unsupported database URL."
        )

    raw_path = database_url[
        len(prefix):
    ]

    if not raw_path:
        raise RuntimeError(
            "SQLite database path is empty."
        )

    path = Path(raw_path).expanduser()

    if not path.is_absolute():
        path = ROOT / path

    return path.resolve()


def _connect() -> sqlite3.Connection:
    path = _sqlite_path()
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        path,
        timeout=15,
    )
    connection.row_factory = (
        sqlite3.Row
    )
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )
    connection.execute(
        "PRAGMA busy_timeout = 15000"
    )
    connection.execute(
        "PRAGMA journal_mode = WAL"
    )
    return connection


def initialize_database() -> None:
    with DATABASE_LOCK:
        with closing(
            _connect()
        ) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS
                schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS
                json_documents (
                    namespace TEXT NOT NULL,
                    document_key TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (
                        namespace,
                        document_key
                    )
                );

                CREATE INDEX IF NOT EXISTS
                idx_json_documents_updated_at
                ON json_documents (
                    updated_at
                );
                """
            )

            connection.execute(
                """
                INSERT OR IGNORE INTO
                schema_migrations (
                    version,
                    applied_at
                )
                VALUES (?, ?)
                """,
                (
                    SCHEMA_VERSION,
                    utc_now(),
                ),
            )
            connection.commit()


def read_document(
    namespace: str,
    document_key: str,
) -> Optional[Dict[str, Any]]:
    initialize_database()

    with DATABASE_LOCK:
        with closing(
            _connect()
        ) as connection:
            row = connection.execute(
                """
                SELECT
                    payload,
                    schema_version,
                    revision,
                    created_at,
                    updated_at
                FROM json_documents
                WHERE
                    namespace = ?
                    AND document_key = ?
                """,
                (
                    namespace,
                    document_key,
                ),
            ).fetchone()

    if row is None:
        return None

    try:
        payload = json.loads(
            row["payload"]
        )
    except json.JSONDecodeError:
        payload = None

    return {
        "payload": payload,
        "schema_version":
            int(row["schema_version"]),
        "revision":
            int(row["revision"]),
        "created_at":
            row["created_at"],
        "updated_at":
            row["updated_at"],
    }


def write_document(
    namespace: str,
    document_key: str,
    payload: Any,
    *,
    schema_version: int = 1,
    expected_revision: Optional[int] = None,
) -> Dict[str, Any]:
    initialize_database()

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    timestamp = utc_now()

    with DATABASE_LOCK:
        with closing(
            _connect()
        ) as connection:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            row = connection.execute(
                """
                SELECT
                    revision,
                    created_at
                FROM json_documents
                WHERE
                    namespace = ?
                    AND document_key = ?
                """,
                (
                    namespace,
                    document_key,
                ),
            ).fetchone()

            current_revision = (
                int(row["revision"])
                if row is not None
                else 0
            )

            if (
                expected_revision
                is not None
                and expected_revision
                    != current_revision
            ):
                connection.rollback()
                raise RevisionConflict(
                    current_revision,
                )

            next_revision = (
                current_revision + 1
            )
            created_at = (
                row["created_at"]
                if row is not None
                else timestamp
            )

            if row is None:
                connection.execute(
                    """
                    INSERT INTO
                    json_documents (
                        namespace,
                        document_key,
                        payload,
                        schema_version,
                        revision,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        namespace,
                        document_key,
                        serialized,
                        schema_version,
                        next_revision,
                        created_at,
                        timestamp,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE json_documents
                    SET
                        payload = ?,
                        schema_version = ?,
                        revision = ?,
                        updated_at = ?
                    WHERE
                        namespace = ?
                        AND document_key = ?
                    """,
                    (
                        serialized,
                        schema_version,
                        next_revision,
                        timestamp,
                        namespace,
                        document_key,
                    ),
                )

            connection.commit()

    return {
        "schema_version":
            schema_version,
        "revision":
            next_revision,
        "created_at":
            created_at,
        "updated_at":
            timestamp,
    }


def read_json_document(
    namespace: str,
    document_key: str,
    *,
    fallback: Any,
    legacy_path: Optional[Path] = None,
) -> Any:
    document = read_document(
        namespace,
        document_key,
    )

    if document is not None:
        return document["payload"]

    if (
        legacy_path is not None
        and legacy_path.exists()
    ):
        try:
            payload = json.loads(
                legacy_path.read_text(
                    encoding="utf-8",
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            payload = fallback

        write_document(
            namespace,
            document_key,
            payload,
            schema_version=1,
            expected_revision=0,
        )
        return payload

    return fallback


def write_json_document(
    namespace: str,
    document_key: str,
    payload: Any,
) -> Dict[str, Any]:
    return write_document(
        namespace,
        document_key,
        payload,
        schema_version=1,
    )


def database_health() -> Dict[str, Any]:
    try:
        initialize_database()

        with DATABASE_LOCK:
            with closing(
                _connect()
            ) as connection:
                row = connection.execute(
                    """
                    SELECT
                        COUNT(*) AS document_count
                    FROM json_documents
                    """
                ).fetchone()

        return {
            "status": "ready",
            "driver": "sqlite",
            "schema_version":
                SCHEMA_VERSION,
            "document_count":
                int(
                    row["document_count"]
                ),
        }
    except Exception as error:
        return {
            "status": "error",
            "driver": "sqlite",
            "schema_version":
                SCHEMA_VERSION,
            "error":
                str(error),
        }
