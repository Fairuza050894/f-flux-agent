"""Application commands for TestRun use cases."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CreateRunCommand:
    project_id: str
    source: str = "ui_testing"
    feature: str = "UI Test"
    test_type: str = "ui"
    environment: str = ""
    request_snapshot: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateProgressCommand:
    run_id: str
    status: Optional[str] = None
    progress: Optional[float] = None
    current_stage: Optional[str] = None
    current_step: Optional[str] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    need_review: Optional[int] = None
    safe_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompleteRunCommand:
    run_id: str
    status: str = "completed"
    progress: float = 100.0
    passed: Optional[int] = None
    failed: Optional[int] = None
    need_review: Optional[int] = None
    result_summary: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FailRunCommand:
    run_id: str
    error_message: str
    safe_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CancelRunCommand:
    run_id: str
    reason: str = ""
