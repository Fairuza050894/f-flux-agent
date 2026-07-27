from __future__ import annotations

from hashlib import sha256
from typing import Literal, Optional
import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from qa_dashboard.backend.database import (
    RevisionConflict,
    read_document,
    write_document,
)


router = APIRouter(
    prefix="/api/v1/account",
    tags=["QA Account"],
)

ACCOUNT_NAMESPACE = "qa_dashboard_account"
ACCOUNT_SCHEMA_VERSION = 1
ALLOWED_THEMES = {"system", "light", "dark"}


class AccountProfileRequest(BaseModel):
    display_name: str = Field(
        default="",
        max_length=80,
    )
    job_title: str = Field(
        default="",
        max_length=80,
    )
    avatar_initials: str = Field(
        default="",
        max_length=3,
    )


class AccountPreferencesRequest(BaseModel):
    theme: Literal[
        "system",
        "light",
        "dark",
    ] = "system"
    default_project_id: str = Field(
        default="",
        max_length=120,
    )
    default_environment_id: str = Field(
        default="",
        max_length=120,
    )


class AccountSettingsRequest(BaseModel):
    profile: AccountProfileRequest = Field(
        default_factory=AccountProfileRequest,
    )
    preferences: AccountPreferencesRequest = Field(
        default_factory=AccountPreferencesRequest,
    )
    expected_revision: Optional[int] = Field(
        default=None,
        ge=0,
    )


def _actor(request: Request):
    actor = getattr(
        request.state,
        "qa_actor",
        None,
    )

    if actor is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "ACCOUNT_SESSION_REQUIRED",
                "message": (
                    "An authenticated dashboard "
                    "session is required."
                ),
            },
        )

    return actor


def _identity_value(
    actor,
    name: str,
) -> str:
    return str(
        getattr(actor, name, "") or ""
    ).strip()


def _identity(actor) -> dict:
    permissions = getattr(
        actor,
        "permissions",
        (),
    )

    return {
        "user_id": _identity_value(
            actor,
            "user_id",
        ),
        "email": _identity_value(
            actor,
            "email",
        ),
        "display_name": _identity_value(
            actor,
            "display_name",
        ),
        "provider": _identity_value(
            actor,
            "provider",
        ),
        "role": _identity_value(
            actor,
            "role",
        ) or "viewer",
        "permissions": list(
            permissions or ()
        ),
    }


def _document_key(actor) -> str:
    identity = _identity(actor)
    raw_key = (
        f"{identity['provider']}:"
        f"{identity['user_id'] or identity['email']}"
    )

    if raw_key == ":":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ACCOUNT_IDENTITY_INVALID",
                "message": (
                    "The authenticated session does "
                    "not contain a stable user identity."
                ),
            },
        )

    return sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


def _initials(value: str) -> str:
    words = [
        item
        for item in re.split(
            r"\s+",
            str(value or "").strip(),
        )
        if item
    ]

    if not words:
        return "U"

    if len(words) == 1:
        return words[0][:2].upper()

    return (
        words[0][0]
        + words[-1][0]
    ).upper()


def _clean_initials(
    value: str,
    fallback: str,
) -> str:
    normalized = re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value or "").strip(),
    )[:3].upper()

    return normalized or _initials(
        fallback
    )


def _default_payload(actor) -> dict:
    identity = _identity(actor)
    display_name = (
        identity["display_name"]
        or identity["email"]
        or identity["user_id"]
        or "Dashboard user"
    )

    return {
        "profile": {
            "display_name": display_name,
            "job_title": "",
            "avatar_initials": _initials(
                display_name
            ),
        },
        "preferences": {
            "theme": "system",
            "default_project_id": "",
            "default_environment_id": "",
        },
    }


def _normalize_payload(
    actor,
    payload,
) -> dict:
    defaults = _default_payload(actor)
    source = (
        payload
        if isinstance(payload, dict)
        else {}
    )
    profile_source = source.get(
        "profile",
        {},
    )
    preferences_source = source.get(
        "preferences",
        {},
    )

    if not isinstance(profile_source, dict):
        profile_source = {}

    if not isinstance(
        preferences_source,
        dict,
    ):
        preferences_source = {}

    display_name = str(
        profile_source.get(
            "display_name",
            defaults["profile"][
                "display_name"
            ],
        )
        or ""
    ).strip()[:80]

    if not display_name:
        display_name = defaults[
            "profile"
        ]["display_name"]

    theme = str(
        preferences_source.get(
            "theme",
            "system",
        )
        or "system"
    ).strip().lower()

    if theme not in ALLOWED_THEMES:
        theme = "system"

    return {
        "profile": {
            "display_name": display_name,
            "job_title": str(
                profile_source.get(
                    "job_title",
                    "",
                )
                or ""
            ).strip()[:80],
            "avatar_initials": (
                _clean_initials(
                    profile_source.get(
                        "avatar_initials",
                        "",
                    ),
                    display_name,
                )
            ),
        },
        "preferences": {
            "theme": theme,
            "default_project_id": str(
                preferences_source.get(
                    "default_project_id",
                    "",
                )
                or ""
            ).strip()[:120],
            "default_environment_id": str(
                preferences_source.get(
                    "default_environment_id",
                    "",
                )
                or ""
            ).strip()[:120],
        },
    }


def _public_response(
    *,
    actor,
    document,
) -> dict:
    if document is None:
        return {
            "exists": False,
            "schema_version": (
                ACCOUNT_SCHEMA_VERSION
            ),
            "revision": 0,
            "created_at": None,
            "updated_at": None,
            "identity": _identity(actor),
            **_default_payload(actor),
        }

    return {
        "exists": True,
        "schema_version": int(
            document.get(
                "schema_version",
                ACCOUNT_SCHEMA_VERSION,
            )
        ),
        "revision": int(
            document.get(
                "revision",
                0,
            )
        ),
        "created_at": document.get(
            "created_at"
        ),
        "updated_at": document.get(
            "updated_at"
        ),
        "identity": _identity(actor),
        **_normalize_payload(
            actor,
            document.get("payload"),
        ),
    }


@router.get("")
def get_account_settings(
    request: Request,
):
    actor = _actor(request)
    document = read_document(
        ACCOUNT_NAMESPACE,
        _document_key(actor),
    )

    return _public_response(
        actor=actor,
        document=document,
    )


def _model_payload(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


@router.put("")
def put_account_settings(
    request: Request,
    payload: AccountSettingsRequest,
):
    actor = _actor(request)
    normalized = _normalize_payload(
        actor,
        {
            "profile": _model_payload(
                payload.profile
            ),
            "preferences": _model_payload(
                payload.preferences
            ),
        },
    )

    try:
        metadata = write_document(
            ACCOUNT_NAMESPACE,
            _document_key(actor),
            normalized,
            schema_version=(
                ACCOUNT_SCHEMA_VERSION
            ),
            expected_revision=(
                payload.expected_revision
            ),
        )
    except RevisionConflict as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": (
                    "ACCOUNT_REVISION_CONFLICT"
                ),
                "message": (
                    "Account settings changed in "
                    "another session. Reload the "
                    "latest settings and try again."
                ),
                "current_revision": (
                    error.current_revision
                ),
            },
        ) from error

    return {
        "ok": True,
        "exists": True,
        "identity": _identity(actor),
        **normalized,
        **metadata,
    }
