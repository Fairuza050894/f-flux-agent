from __future__ import annotations

from typing import Any, Dict, Optional
import json

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field

from qa_dashboard.backend.database import (
    RevisionConflict,
    database_health,
    read_document,
    write_document,
)
from qa_dashboard.backend.settings import (
    get_settings,
)


router = APIRouter(
    prefix="/api/v1/workspace",
    tags=["QA Workspace"],
)

WORKSPACE_NAMESPACE = (
    "qa_dashboard_workspace"
)
MAX_WORKSPACE_BYTES = (
    15 * 1024 * 1024
)
ALLOWED_STATE_KEYS = {
    "projectEnvironment",
    "testAssets",
    "testPlans",
    "testCycles",
}


class WorkspaceStateRequest(
    BaseModel,
):
    state: Dict[str, Any]
    schema_version: int = Field(
        default=1,
        ge=1,
        le=100,
    )
    expected_revision: Optional[int] = Field(
            default=None,
            ge=0,
        )
    source: str = Field(
        default="frontend-sync",
        min_length=1,
        max_length=120,
    )


def _workspace_id() -> str:
    return get_settings().workspace_id


def _validate_state(
    state: Dict[str, Any],
) -> None:
    unknown_keys = (
        set(state.keys())
        - ALLOWED_STATE_KEYS
    )

    if unknown_keys:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "WORKSPACE_STATE_INVALID",
                "message":
                    "Unsupported workspace "
                    "state sections.",
                "unknown_keys":
                    sorted(unknown_keys),
            },
        )

    invalid_sections = [
        key
        for key, value in state.items()
        if not isinstance(
            value,
            dict,
        )
    ]

    if invalid_sections:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "WORKSPACE_STATE_INVALID",
                "message":
                    "Workspace state sections "
                    "must be objects.",
                "invalid_sections":
                    invalid_sections,
            },
        )

    serialized = json.dumps(
        state,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    if (
        len(serialized)
        > MAX_WORKSPACE_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail={
                "code":
                    "WORKSPACE_STATE_TOO_LARGE",
                "message":
                    "Workspace state exceeds "
                    "the 15 MB limit.",
            },
        )


@router.get(
    "/state",
)
def get_workspace_state():
    workspace_id = _workspace_id()
    document = read_document(
        WORKSPACE_NAMESPACE,
        workspace_id,
    )

    if document is None:
        return {
            "exists": False,
            "workspace_id":
                workspace_id,
            "schema_version": 1,
            "revision": 0,
            "created_at": None,
            "updated_at": None,
            "state": {},
            "source": None,
        }

    payload = (
        document["payload"]
        if isinstance(
            document["payload"],
            dict,
        )
        else {}
    )

    return {
        "exists": True,
        "workspace_id":
            workspace_id,
        "schema_version":
            document[
                "schema_version"
            ],
        "revision":
            document["revision"],
        "created_at":
            document["created_at"],
        "updated_at":
            document["updated_at"],
        "state":
            payload.get(
                "state",
                {},
            ),
        "source":
            payload.get("source"),
    }


@router.put(
    "/state",
)
def put_workspace_state(
    request: WorkspaceStateRequest,
):
    if not get_settings().sync_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code":
                    "WORKSPACE_SYNC_DISABLED",
                "message":
                    "Workspace synchronization "
                    "is disabled.",
            },
        )

    _validate_state(
        request.state,
    )

    workspace_id = _workspace_id()

    try:
        metadata = write_document(
            WORKSPACE_NAMESPACE,
            workspace_id,
            {
                "state": request.state,
                "source": request.source,
            },
            schema_version=
                request.schema_version,
            expected_revision=
                request.expected_revision,
        )
    except RevisionConflict as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "WORKSPACE_REVISION_CONFLICT",
                "message":
                    "The workspace changed "
                    "on another client.",
                "current_revision":
                    error.current_revision,
            },
        ) from error

    return {
        "ok": True,
        "workspace_id":
            workspace_id,
        **metadata,
    }


@router.get(
    "/health",
)
def workspace_health():
    return {
        "workspace_id":
            _workspace_id(),
        "sync_enabled":
            get_settings().sync_enabled,
        "database":
            database_health(),
    }
