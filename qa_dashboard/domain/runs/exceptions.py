"""Domain exceptions for Test Runs."""


class RunDomainError(Exception):
    """Base domain exception for Test Run operations."""
    pass


class InvalidStateTransitionError(RunDomainError):
    """Raised when an invalid state transition is attempted on a TestRun."""

    def __init__(self, current_status: str, target_status: str, message: str = ""):
        self.current_status = current_status
        self.target_status = target_status
        details = f": {message}" if message else ""
        super().__init__(
            f"Invalid transition from {current_status} to {target_status}{details}"
        )


class RunNotFoundError(RunDomainError):
    """Raised when a requested TestRun does not exist."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        super().__init__(f"TestRun not found: {run_id}")


class InvalidRunDataError(RunDomainError):
    """Raised when TestRun input invariants are violated."""
    pass
