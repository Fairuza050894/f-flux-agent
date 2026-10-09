"""Pure domain entity for Test Runs."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from qa_dashboard.domain.runs.enums import RunSource, RunStatus
from qa_dashboard.domain.runs.exceptions import (
    InvalidRunDataError,
    InvalidStateTransitionError,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TestRun:
    """Domain model representing an end-to-end QA Test Run execution."""

    run_id: str
    project_id: str
    source: RunSource
    feature: str
    test_type: str = "ui"
    environment: str = ""
    status: RunStatus = RunStatus.QUEUED
    progress: float = 0.0
    current_stage: str = "queued"
    current_step: str = ""
    passed: int = 0
    failed: int = 0
    need_review: int = 0
    request_snapshot: Dict[str, Any] = field(default_factory=dict)
    safe_metadata: Dict[str, Any] = field(default_factory=dict)
    result_summary: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    created_at: str = field(default_factory=utc_now)
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=utc_now)
    completed_at: Optional[str] = None

    @classmethod
    def create(
        cls,
        project_id: str,
        source: RunSource,
        feature: str,
        test_type: str = "ui",
        environment: str = "",
        request_snapshot: Optional[Dict[str, Any]] = None,
    ) -> "TestRun":
        if not project_id or not project_id.strip():
            raise InvalidRunDataError("project_id must not be empty")

        now = utc_now()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        run_id = f"run-{timestamp}-{uuid4().hex[:8]}"

        return cls(
            run_id=run_id,
            project_id=project_id.strip(),
            source=source,
            feature=feature.strip() or "UI Test",
            test_type=test_type.strip() or "ui",
            environment=environment.strip(),
            status=RunStatus.QUEUED,
            progress=0.0,
            current_stage="queued",
            current_step="",
            passed=0,
            failed=0,
            need_review=0,
            request_snapshot=request_snapshot or {},
            safe_metadata={},
            result_summary={},
            artifacts=[],
            error_message="",
            created_at=now,
            started_at=None,
            updated_at=now,
            completed_at=None,
        )

    def start(self, at_time: Optional[str] = None) -> None:
        if self.status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                RunStatus.RUNNING.value,
                "terminal run cannot be restarted",
            )
        now = at_time or utc_now()
        self.status = RunStatus.RUNNING
        if not self.started_at:
            self.started_at = now
        self.updated_at = now

    def update_progress(
        self,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        current_stage: Optional[str] = None,
        current_step: Optional[str] = None,
        passed: Optional[int] = None,
        failed: Optional[int] = None,
        need_review: Optional[int] = None,
        safe_metadata: Optional[Dict[str, Any]] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        if self.status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                "progress_update",
                "terminal run cannot receive progress updates",
            )

        now = updated_at or utc_now()

        if status:
            target_status = RunStatus.from_string(status)
            if target_status.is_terminal:
                raise InvalidStateTransitionError(
                    self.status.value,
                    target_status.value,
                    "use complete() or fail() to transition to terminal states",
                )
            self.status = target_status

        if not self.started_at and self.status in {RunStatus.RUNNING, RunStatus.EXECUTING}:
            self.started_at = now

        if progress is not None:
            prog = float(progress)
            if prog < 0 or prog > 100:
                raise InvalidRunDataError("Progress must be between 0 and 100")
            self.progress = prog

        if current_stage is not None:
            self.current_stage = str(current_stage).strip()

        if current_step is not None:
            self.current_step = str(current_step).strip()

        if passed is not None:
            if passed < 0:
                raise InvalidRunDataError("passed count must be non-negative")
            self.passed = passed

        if failed is not None:
            if failed < 0:
                raise InvalidRunDataError("failed count must be non-negative")
            self.failed = failed

        if need_review is not None:
            if need_review < 0:
                raise InvalidRunDataError("need_review count must be non-negative")
            self.need_review = need_review

        if safe_metadata:
            self.safe_metadata.update(safe_metadata)

        self.updated_at = now

    def complete(
        self,
        status: RunStatus = RunStatus.COMPLETED,
        progress: float = 100.0,
        passed: Optional[int] = None,
        failed: Optional[int] = None,
        need_review: Optional[int] = None,
        result_summary: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        completed_at: Optional[str] = None,
    ) -> None:
        if self.status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                status.value,
                "run is already in a terminal state",
            )

        if not status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                status.value,
                "completion requires a terminal status",
            )

        now = completed_at or utc_now()
        self.status = status
        self.progress = float(progress)
        self.current_stage = "completed"
        self.current_step = ""

        if passed is not None:
            self.passed = passed
        if failed is not None:
            self.failed = failed
        if need_review is not None:
            self.need_review = need_review
        if result_summary:
            self.result_summary = result_summary
        if artifacts:
            self.artifacts = artifacts

        if not self.started_at:
            self.started_at = self.created_at or now

        self.updated_at = now
        self.completed_at = now

    def fail(
        self,
        error_message: str,
        safe_metadata: Optional[Dict[str, Any]] = None,
        failed_at: Optional[str] = None,
    ) -> None:
        if self.status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                RunStatus.FAILED.value,
                "run is already in a terminal state",
            )

        now = failed_at or utc_now()
        self.status = RunStatus.FAILED
        self.current_stage = "failed"
        self.current_step = ""
        self.error_message = str(error_message or "").strip()

        if safe_metadata:
            self.safe_metadata.update(safe_metadata)

        if not self.started_at:
            self.started_at = self.created_at or now

        self.updated_at = now
        self.completed_at = now

    def cancel(self, reason: str = "", cancelled_at: Optional[str] = None) -> None:
        if self.status.is_terminal:
            raise InvalidStateTransitionError(
                self.status.value,
                RunStatus.CANCELLED.value,
                "run is already in a terminal state",
            )

        now = cancelled_at or utc_now()
        self.status = RunStatus.CANCELLED
        self.current_stage = "cancelled"
        self.current_step = ""
        if reason:
            self.error_message = reason

        self.updated_at = now
        self.completed_at = now
