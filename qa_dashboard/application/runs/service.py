"""Application service orchestrating TestRun use cases."""

from typing import List, Optional

from qa_dashboard.application.runs.commands import (
    CancelRunCommand,
    CompleteRunCommand,
    CreateRunCommand,
    FailRunCommand,
    UpdateProgressCommand,
)
from qa_dashboard.application.runs.dto import RunDTO
from qa_dashboard.domain.runs.entities import TestRun
from qa_dashboard.domain.runs.enums import RunSource, RunStatus
from qa_dashboard.domain.runs.exceptions import RunNotFoundError
from qa_dashboard.ports.run_repository import RunRepository


class RunService:
    """Application service for managing TestRun lifecycles."""

    def __init__(self, repository: RunRepository):
        self._repository = repository

    def create_run(self, cmd: CreateRunCommand) -> RunDTO:
        source = RunSource.from_string(cmd.source)
        run = TestRun.create(
            project_id=cmd.project_id,
            source=source,
            feature=cmd.feature,
            test_type=cmd.test_type,
            environment=cmd.environment,
            request_snapshot=cmd.request_snapshot,
        )
        saved = self._repository.save(run)
        return RunDTO.from_entity(saved)

    def get_run(self, run_id: str) -> RunDTO:
        run = self._repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        return RunDTO.from_entity(run)

    def list_active(
        self,
        project_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[RunDTO]:
        runs = self._repository.list_active(project_id=project_id, source=source)
        return [RunDTO.from_entity(r) for r in runs]

    def update_progress(self, cmd: UpdateProgressCommand) -> RunDTO:
        run = self._repository.get(cmd.run_id)
        if not run:
            raise RunNotFoundError(cmd.run_id)

        run.update_progress(
            status=cmd.status,
            progress=cmd.progress,
            current_stage=cmd.current_stage,
            current_step=cmd.current_step,
            passed=cmd.passed,
            failed=cmd.failed,
            need_review=cmd.need_review,
            safe_metadata=cmd.safe_metadata,
        )
        saved = self._repository.save(run)
        return RunDTO.from_entity(saved)

    def complete_run(self, cmd: CompleteRunCommand) -> RunDTO:
        run = self._repository.get(cmd.run_id)
        if not run:
            raise RunNotFoundError(cmd.run_id)

        target_status = RunStatus.from_string(cmd.status)
        run.complete(
            status=target_status,
            progress=cmd.progress,
            passed=cmd.passed,
            failed=cmd.failed,
            need_review=cmd.need_review,
            result_summary=cmd.result_summary,
            artifacts=cmd.artifacts,
        )
        saved = self._repository.save(run)
        return RunDTO.from_entity(saved)

    def fail_run(self, cmd: FailRunCommand) -> RunDTO:
        run = self._repository.get(cmd.run_id)
        if not run:
            raise RunNotFoundError(cmd.run_id)

        run.fail(
            error_message=cmd.error_message,
            safe_metadata=cmd.safe_metadata,
        )
        saved = self._repository.save(run)
        return RunDTO.from_entity(saved)

    def cancel_run(self, cmd: CancelRunCommand) -> RunDTO:
        run = self._repository.get(cmd.run_id)
        if not run:
            raise RunNotFoundError(cmd.run_id)

        run.cancel(reason=cmd.reason)
        saved = self._repository.save(run)
        return RunDTO.from_entity(saved)
