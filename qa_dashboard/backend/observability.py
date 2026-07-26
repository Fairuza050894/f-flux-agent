from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Query,
    Request,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from qa_dashboard.backend.audit_service import (
    list_events,
)
from qa_dashboard.backend.reliability import (
    incident_snapshot,
    liveness_snapshot,
    operations_snapshot,
    readiness_snapshot,
    recover_stale_executions,
)


router = APIRouter(
    tags=["QA Operations"],
)


class StaleRecoveryRequest(BaseModel):
    dry_run: bool = True
    reason: str = Field(
        default="",
        max_length=500,
    )


def _actor_values(
    request: Request,
) -> tuple[str, str]:
    actor = getattr(
        request.state,
        "qa_actor",
        None,
    )

    if actor is None:
        return "system", ""

    return (
        str(
            getattr(
                actor,
                "email",
                "",
            )
            or getattr(
                actor,
                "user_id",
                "",
            )
            or "system"
        ),
        str(
            getattr(
                actor,
                "role",
                "",
            )
        ),
    )


@router.get(
    "/api/v1/health/live",
)
def health_live():
    return liveness_snapshot()


@router.get(
    "/api/v1/health/ready",
)
def health_ready():
    payload = readiness_snapshot()

    return JSONResponse(
        status_code=(
            200
            if payload.get("ready")
            else 503
        ),
        content=payload,
    )


@router.get(
    "/api/v1/operations/status",
)
def operations_status():
    return operations_snapshot()


@router.get(
    "/api/v1/operations/audit-events",
)
def operations_audit_events(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    category: str = Query(
        default="",
        max_length=80,
    ),
    action: str = Query(
        default="",
        max_length=160,
    ),
    result: str = Query(
        default="",
        max_length=40,
    ),
    actor: str = Query(
        default="",
        max_length=240,
    ),
    request_id: str = Query(
        default="",
        max_length=160,
    ),
    include_authentication: bool = True,
):
    return list_events(
        limit=limit,
        category=category,
        action=action,
        result=result,
        actor=actor,
        request_id=request_id,
        include_authentication=
            include_authentication,
    )


@router.get(
    "/api/v1/operations/incidents",
)
def operations_incidents():
    return incident_snapshot()


@router.post(
    "/api/v1/operations/recovery/stale-executions",
)
def operations_recover_stale_executions(
    request: Request,
    payload: StaleRecoveryRequest,
):
    actor, actor_role = _actor_values(
        request
    )

    return recover_stale_executions(
        dry_run=payload.dry_run,
        reason=payload.reason.strip(),
        actor=actor,
        actor_role=actor_role,
        request_id=str(
            getattr(
                request.state,
                "request_id",
                "",
            )
        ),
    )
