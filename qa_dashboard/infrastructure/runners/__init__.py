"""Runner infrastructure package – RunnerRegistry.

Maps test-type strings to :class:`~qa_dashboard.ports.execution_runner.ExecutionRunner`
implementations.  Add a new runner by calling :meth:`RunnerRegistry.register`.

Supported runner types (Phase-02)
-----------------------------------
``browser`` / ``ui``
    :class:`~qa_dashboard.infrastructure.runners.browser_runner.BrowserExecutionRunner`
    – Playwright-backed UI execution via checker.py.

``api`` / ``curl``
    :class:`~qa_dashboard.infrastructure.runners.api_runner.ApiExecutionRunner`
    – urllib-backed HTTP execution (for API / cURL tests).

``legacy`` / ``registered``
    :class:`~qa_dashboard.infrastructure.runners.api_runner.LegacyCheckerAdapter`
    – Thin adapter that calls ``perform_audit_for_telegram`` directly.
"""

from __future__ import annotations

from typing import Dict

from qa_dashboard.ports.execution_runner import ExecutionRunner


class RunnerRegistry:
    """Lightweight registry mapping runner-type strings to runner instances.

    The registry is a singleton-like object; the module-level ``default_registry``
    instance is pre-populated with the built-in runners.

    Usage::

        runner = default_registry.resolve("browser")
        result = runner.run(request)
    """

    def __init__(self) -> None:
        self._registry: Dict[str, ExecutionRunner] = {}

    def register(self, key: str, runner: ExecutionRunner) -> None:
        """Register *runner* under *key* (case-insensitive)."""
        self._registry[key.strip().lower()] = runner

    def resolve(self, runner_type: str) -> ExecutionRunner:
        """Return the runner registered for *runner_type*.

        Raises :class:`KeyError` if no runner is registered for the type.

        Parameters
        ----------
        runner_type:
            Type string, e.g. ``"browser"``, ``"api"``, ``"legacy"``.
        """
        key = (runner_type or "browser").strip().lower()
        if key not in self._registry:
            available = sorted(self._registry.keys())
            raise KeyError(
                f"No runner registered for type '{key}'. "
                f"Available: {available}"
            )
        return self._registry[key]

    def available_types(self) -> list:
        return sorted(self._registry.keys())


def _build_default_registry() -> RunnerRegistry:
    from qa_dashboard.infrastructure.runners.browser_runner import BrowserExecutionRunner
    from qa_dashboard.infrastructure.runners.api_runner import ApiExecutionRunner, LegacyCheckerAdapter

    registry = RunnerRegistry()
    browser = BrowserExecutionRunner()
    api = ApiExecutionRunner()
    legacy = LegacyCheckerAdapter()

    registry.register("browser", browser)
    registry.register("ui", browser)
    registry.register("api", api)
    registry.register("curl", api)
    registry.register("legacy", legacy)
    registry.register("registered", legacy)

    return registry


# Module-level default registry, lazily initialised on first access.
_default_registry: "RunnerRegistry | None" = None


def get_default_registry() -> RunnerRegistry:
    """Return (and lazily build) the module-level default runner registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = _build_default_registry()
    return _default_registry
