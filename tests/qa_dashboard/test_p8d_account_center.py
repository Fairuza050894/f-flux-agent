from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from qa_dashboard.backend import (
    account_api,
    security,
)
from qa_dashboard.backend.database import (
    RevisionConflict,
)
from qa_dashboard.backend.frontend import (
    is_spa_route,
)


class DummyRequest:
    def __init__(self, actor):
        self.state = SimpleNamespace(
            qa_actor=actor,
            request_id="req-account-test",
        )


def actor():
    return SimpleNamespace(
        user_id="admin",
        email="admin@example.test",
        display_name="Admin",
        provider="basic",
        role="admin",
        permissions=("*",),
    )


def test_account_document_key_is_stable_and_private():
    first = account_api._document_key(
        actor()
    )
    second = account_api._document_key(
        actor()
    )

    assert first == second
    assert len(first) == 64
    assert "admin" not in first
    assert "example" not in first


def test_account_defaults_use_session_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        account_api,
        "read_document",
        lambda *_args, **_kwargs: None,
    )

    result = account_api.get_account_settings(
        DummyRequest(actor())
    )

    assert result["exists"] is False
    assert result["revision"] == 0
    assert result["identity"]["role"] == "admin"
    assert result["profile"]["display_name"] == "Admin"
    assert result["profile"]["avatar_initials"] == "AD"
    assert result["preferences"]["theme"] == "system"


def test_account_update_persists_profile_and_preferences(
    monkeypatch,
):
    captured = {}

    def fake_write(
        namespace,
        document_key,
        payload,
        **options,
    ):
        captured.update({
            "namespace": namespace,
            "document_key": document_key,
            "payload": payload,
            "options": options,
        })
        return {
            "schema_version": 1,
            "revision": 3,
            "created_at": "created",
            "updated_at": "updated",
        }

    monkeypatch.setattr(
        account_api,
        "write_document",
        fake_write,
    )

    request = account_api.AccountSettingsRequest(
        profile={
            "display_name": "Fairuza Restu",
            "job_title": "QA Lead",
            "avatar_initials": "FR",
        },
        preferences={
            "theme": "dark",
            "default_project_id": "mobospace",
            "default_environment_id": (
                "mobospace-sandbox"
            ),
        },
        expected_revision=2,
    )

    result = account_api.put_account_settings(
        DummyRequest(actor()),
        request,
    )

    assert captured["namespace"] == (
        account_api.ACCOUNT_NAMESPACE
    )
    assert captured["options"][
        "expected_revision"
    ] == 2
    assert captured["payload"]["profile"] == {
        "display_name": "Fairuza Restu",
        "job_title": "QA Lead",
        "avatar_initials": "FR",
    }
    assert result["revision"] == 3
    assert result["preferences"]["theme"] == "dark"


def test_account_revision_conflict_returns_409(
    monkeypatch,
):
    def conflict(*_args, **_kwargs):
        raise RevisionConflict(7)

    monkeypatch.setattr(
        account_api,
        "write_document",
        conflict,
    )

    with pytest.raises(HTTPException) as caught:
        account_api.put_account_settings(
            DummyRequest(actor()),
            account_api.AccountSettingsRequest(
                expected_revision=2,
            ),
        )

    assert caught.value.status_code == 409
    assert caught.value.detail[
        "current_revision"
    ] == 7


def test_account_write_is_available_to_viewer_role():
    assert security._required_role(
        "PUT",
        "/api/v1/account",
    ) == "viewer"


def test_account_page_is_a_production_spa_route():
    assert is_spa_route("account") is True
