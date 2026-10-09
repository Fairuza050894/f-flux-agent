"""Domain enumerations for Test Runs."""

from enum import Enum
from typing import Set


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    IN_PROGRESS = "in_progress"
    STARTED = "started"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    NEED_REVIEW = "need_review"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, value: str) -> "RunStatus":
        normalized = (
            str(value or "")
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )
        try:
            return cls(normalized)
        except ValueError:
            # Map common aliases
            if normalized in {"in_progress", "started", "executing"}:
                return cls.RUNNING
            raise ValueError(f"Unknown run status: {value}")

    @property
    def is_active(self) -> bool:
        return self in ACTIVE_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self in TERMINAL_STATUSES


ACTIVE_STATUSES: Set[RunStatus] = {
    RunStatus.QUEUED,
    RunStatus.RUNNING,
    RunStatus.IN_PROGRESS,
    RunStatus.STARTED,
    RunStatus.EXECUTING,
}

TERMINAL_STATUSES: Set[RunStatus] = {
    RunStatus.COMPLETED,
    RunStatus.PASSED,
    RunStatus.FAILED,
    RunStatus.NEED_REVIEW,
    RunStatus.CANCELLED,
}


class RunSource(str, Enum):
    UI_TESTING = "ui_testing"
    API_TESTING = "api_testing"
    REGRESSION_TESTING = "regression_testing"
    UNIT_TESTING = "unit_testing"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str) -> "RunSource":
        normalized = str(value or "other").strip().lower()
        try:
            return cls(normalized)
        except ValueError:
            return cls.OTHER
