"""File-based implementation of RunRepository port."""

from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
import json
import os
import tempfile

from qa_dashboard.domain.runs.entities import TestRun
from qa_dashboard.domain.runs.enums import RunSource, RunStatus
from qa_dashboard.ports.run_repository import RunRepository

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE_PATH = (
    ROOT
    / "skills"
    / "qa_automation"
    / "artifacts"
    / "runtime"
    / "active_runs.json"
)

SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "cookies",
    "session",
    "api_key",
    "apikey",
    "credential",
    "credentials",
}


def is_sensitive_key(value: str) -> bool:
    key = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return key in SENSITIVE_KEYS or any(s in key for s in SENSITIVE_KEYS)


def sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "[MAX_DEPTH]"
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for key, nested in value.items():
            key_text = str(key)
            if is_sensitive_key(key_text):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = sanitize_value(nested, depth + 1)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [sanitize_value(item, depth + 1) for item in value[:500]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class FileRunRepository(RunRepository):
    """File-backed atomic JSON store implementing RunRepository port."""

    def __init__(self, store_path: Optional[Path] = None):
        self._store_path = Path(store_path) if store_path else DEFAULT_STORE_PATH
        self._lock = RLock()
        self._store_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_store(self) -> Dict[str, Any]:
        with self._lock:
            if not self._store_path.exists():
                return {"version": "2.2.1", "runs": {}}
            try:
                payload = json.loads(self._store_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {"version": "2.2.1", "runs": {}}
            if not isinstance(payload, dict):
                return {"version": "2.2.1", "runs": {}}
            if not isinstance(payload.get("runs"), dict):
                payload["runs"] = {}
            payload.setdefault("version", "2.2.1")
            return payload

    def _write_store(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            fd, temp_name = tempfile.mkstemp(
                prefix="active_runs_",
                suffix=".json",
                dir=str(self._store_path.parent),
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(serialized)
                os.replace(temp_name, self._store_path)
            finally:
                if os.path.exists(temp_name):
                    try:
                        os.unlink(temp_name)
                    except OSError:
                        pass

    def _to_entity(self, data: Dict[str, Any]) -> TestRun:
        return TestRun(
            run_id=str(data["run_id"]),
            project_id=str(data.get("project_id", "")),
            source=RunSource.from_string(data.get("source", "other")),
            feature=str(data.get("feature", "UI Test")),
            test_type=str(data.get("test_type", "ui")),
            environment=str(data.get("environment", "")),
            status=RunStatus.from_string(data.get("status", "queued")),
            progress=float(data.get("progress", 0.0)),
            current_stage=str(data.get("current_stage", "")),
            current_step=str(data.get("current_step", "")),
            passed=int(data.get("passed", 0)),
            failed=int(data.get("failed", 0)),
            need_review=int(data.get("need_review", 0)),
            request_snapshot=sanitize_value(data.get("request_snapshot", {})),
            safe_metadata=sanitize_value(data.get("safe_metadata", {})),
            result_summary=sanitize_value(data.get("result_summary", {})),
            artifacts=sanitize_value(data.get("artifacts", [])),
            error_message=str(data.get("error_message", "")),
            created_at=str(data.get("created_at", "")),
            started_at=data.get("started_at"),
            updated_at=str(data.get("updated_at", "")),
            completed_at=data.get("completed_at"),
        )

    def _to_dict(self, run: TestRun) -> Dict[str, Any]:
        return {
            "run_id": run.run_id,
            "project_id": run.project_id,
            "source": run.source.value,
            "feature": run.feature,
            "test_type": run.test_type,
            "environment": run.environment,
            "status": run.status.value,
            "progress": run.progress,
            "current_stage": run.current_stage,
            "current_step": run.current_step,
            "passed": run.passed,
            "failed": run.failed,
            "need_review": run.need_review,
            "request_snapshot": sanitize_value(run.request_snapshot),
            "safe_metadata": sanitize_value(run.safe_metadata),
            "result_summary": sanitize_value(run.result_summary),
            "artifacts": sanitize_value(run.artifacts),
            "error_message": run.error_message,
            "created_at": run.created_at,
            "started_at": run.started_at,
            "updated_at": run.updated_at,
            "completed_at": run.completed_at,
        }

    def save(self, run: TestRun) -> TestRun:
        store = self._read_store()
        store["runs"][run.run_id] = self._to_dict(run)
        self._write_store(store)
        return run

    def get(self, run_id: str) -> Optional[TestRun]:
        store = self._read_store()
        data = store["runs"].get(run_id)
        if not isinstance(data, dict):
            return None
        return self._to_entity(data)

    def list_active(
        self,
        project_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[TestRun]:
        store = self._read_store()
        runs: List[TestRun] = []
        for data in store["runs"].values():
            if not isinstance(data, dict):
                continue
            entity = self._to_entity(data)
            if not entity.status.is_active:
                continue
            if project_id and entity.project_id != project_id:
                continue
            if source and entity.source.value != source:
                continue
            runs.append(entity)

        runs.sort(
            key=lambda r: (r.started_at or r.created_at or ""),
            reverse=True,
        )
        return runs
