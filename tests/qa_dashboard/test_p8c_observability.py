from qa_dashboard.backend.audit_service import (
    derive_http_action,
    sanitize_value,
)


def test_sensitive_values_are_redacted():
    payload = sanitize_value({
        "username": "qa-user",
        "password": "not-for-logs",
        "nested": {
            "Authorization":
                "Bearer secret-token",
        },
    })

    assert payload["username"] == "qa-user"
    assert payload["password"] == "[REDACTED]"
    assert (
        payload["nested"]["Authorization"]
        == "[REDACTED]"
    )


def test_execution_actions_are_classified():
    assert derive_http_action(
        "POST",
        "/api/v1/executions/run-1/dispatch",
    ) == (
        "execution.dispatched",
        "execution",
    )

    assert derive_http_action(
        "POST",
        "/api/v1/operations/recovery/stale-executions",
    ) == (
        "execution.recovery_requested",
        "reliability",
    )
