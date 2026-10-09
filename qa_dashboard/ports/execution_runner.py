"""ExecutionRunner port definition and execution contracts."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ExecutionRequest:
    """Contract representing an instruction to execute a test suite or case."""
    run_id: str
    feature: str
    test_type: str
    target_url: str
    mode: str = "smoke"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseResult:
    """Contract representing the outcome of a single test assertion or step."""
    id: str
    title: str
    status: str  # "PASS", "FAILED", "NEED REVIEW"
    details: str = ""


@dataclass
class ExecutionResult:
    """Deterministic execution outcome with optional AI analysis enrichment."""
    status: str  # Deterministic: "PASS", "FAILED", "NEED REVIEW"
    test_cases: List[TestCaseResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    need_review: int = 0
    artifacts: Dict[str, str] = field(default_factory=dict)
    summary: str = ""
    error_message: str = ""
    # AI enrichment is strictly optional and does NOT drive PASS/FAIL status
    ai_analysis: Optional[Dict[str, Any]] = None


class ExecutionRunner(Protocol):
    """Port for test execution runners (browser, API, CLI)."""

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute the test run synchronously or return execution handle."""
        ...
