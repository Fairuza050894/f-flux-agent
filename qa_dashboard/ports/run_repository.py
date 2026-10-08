"""RunRepository port definition."""

from typing import List, Optional, Protocol
from qa_dashboard.domain.runs.entities import TestRun


class RunRepository(Protocol):
    """Port for TestRun persistence."""

    def save(self, run: TestRun) -> TestRun:
        """Persist or update a TestRun entity."""
        ...

    def get(self, run_id: str) -> Optional[TestRun]:
        """Retrieve a TestRun entity by its unique ID."""
        ...

    def list_active(
        self,
        project_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[TestRun]:
        """List all runs currently in an active (non-terminal) state."""
        ...
