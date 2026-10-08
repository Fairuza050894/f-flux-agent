"""Data Transfer Objects for Test Runs."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from qa_dashboard.domain.runs.entities import TestRun


@dataclass
class RunDTO:
    run_id: str
    project_id: str
    source: str
    feature: str
    test_type: str
    environment: str
    status: str
    progress: float
    current_stage: str
    current_step: str
    passed: int
    failed: int
    need_review: int
    request_snapshot: Dict[str, Any]
    safe_metadata: Dict[str, Any]
    result_summary: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    error_message: str
    created_at: str
    started_at: Optional[str]
    updated_at: str
    completed_at: Optional[str]

    @classmethod
    def from_entity(cls, entity: TestRun) -> "RunDTO":
        return cls(
            run_id=entity.run_id,
            project_id=entity.project_id,
            source=entity.source.value,
            feature=entity.feature,
            test_type=entity.test_type,
            environment=entity.environment,
            status=entity.status.value,
            progress=entity.progress,
            current_stage=entity.current_stage,
            current_step=entity.current_step,
            passed=entity.passed,
            failed=entity.failed,
            need_review=entity.need_review,
            request_snapshot=entity.request_snapshot,
            safe_metadata=entity.safe_metadata,
            result_summary=entity.result_summary,
            artifacts=entity.artifacts,
            error_message=entity.error_message,
            created_at=entity.created_at,
            started_at=entity.started_at,
            updated_at=entity.updated_at,
            completed_at=entity.completed_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
