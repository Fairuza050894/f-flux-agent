"""
Veriflow Trigger Skill for Hermes.

Triggers Veriflow QA automation runs via REST API and retrieves cinematic reports.
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from hermes_constants import get_hermes_home


class VeriflowClient:
    """Client for Veriflow API."""

    def __init__(self, base_url: str = "http://localhost:3000", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def health_check(self) -> Dict[str, Any]:
        """Check if Veriflow is healthy."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/health", headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def quick_run(self, repo_url: str, name: str = "") -> Dict[str, Any]:
        """Trigger a quick QA run."""
        payload = {"repo_url": repo_url}
        if name:
            payload["name"] = name
        try:
            resp = self.client.post(
                f"{self.base_url}/api/v1/projects/quick-run",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def create_run(
        self,
        repo_url: str,
        name: str,
        feature: str = "",
        mode: str = "regression",
    ) -> Dict[str, Any]:
        """Create a custom QA run."""
        payload = {
            "repo_url": repo_url,
            "name": name,
            "feature": feature,
            "mode": mode,
        }
        try:
            resp = self.client.post(
                f"{self.base_url}/api/v1/projects",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            project = resp.json()

            # Start run
            run_resp = self.client.post(
                f"{self.base_url}/api/v1/projects/{project['id']}/runs",
                headers=self._headers(),
                json={"mode": mode},
            )
            run_resp.raise_for_status()
            return run_resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get run status."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/v1/runs/{run_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_run_logs(self, run_id: str) -> str:
        """Get run logs (SSE stream)."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/v1/runs/{run_id}/logs",
                headers=self._headers(),
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            return f"Error fetching logs: {e}"

    def get_report(self, run_id: str, format: str = "html") -> Dict[str, Any]:
        """Get run report."""
        try:
            resp = self.client.get(
                f"{self.base_url}/api/v1/runs/{run_id}/report",
                headers=self._headers(),
                params={"format": format},
            )
            resp.raise_for_status()
            if format == "json":
                return resp.json()
            return {"content": resp.text, "format": format}
        except Exception as e:
            return {"error": str(e)}

    def list_runs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List runs."""
        try:
            params = {}
            if project_id:
                params["project_id"] = project_id
            resp = self.client.get(
                f"{self.base_url}/api/v1/runs",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return [{"error": str(e)}]


def _load_config() -> Dict[str, Any]:
    """Load skill config from Hermes config.yaml."""
    import yaml

    config_path = get_hermes_home() / "config.yaml"
    if not config_path.exists():
        return {}

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return config.get("skills", {}).get("config", {}).get("veriflow_trigger", {})
    except Exception:
        return {}


def _get_client() -> VeriflowClient:
    """Get configured Veriflow client."""
    config = _load_config()
    base_url = config.get("veriflow_base_url", "http://localhost:3000")
    api_key = config.get("veriflow_api_key", "")
    return VeriflowClient(base_url, api_key)


# Main skill functions
def run_veriflow_qa(
    repo_url: str = "",
    name: str = "",
    feature: str = "",
    mode: str = "regression",
) -> str:
    """
    Trigger a Veriflow QA run.

    Args:
        repo_url: Repository URL to test
        name: Project name (optional)
        feature: Specific feature to test (optional)
        mode: smoke | regression | full

    Returns:
        JSON string with run_id and status
    """
    config = _load_config()
    default_repo = config.get("default_repo", "https://github.com/Fairuza050894/LogiTrack")

    client = _get_client()

    if not repo_url:
        repo_url = default_repo

    if not name:
        name = repo_url.split("/")[-1].replace(".git", "")

    result = client.create_run(repo_url, name, feature, mode)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps(
        {
            "success": True,
            "run_id": result.get("id"),
            "project_id": result.get("project_id"),
            "status": result.get("status", "pending"),
            "message": f"Veriflow run started for {name}",
            "monitor_url": f"{client.base_url}/runs/{result.get('id')}",
        }
    )


def get_veriflow_status(run_id: str) -> str:
    """Get status of a Veriflow run."""
    client = _get_client()
    result = client.get_run_status(run_id)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps({"success": True, **result})


def get_veriflow_report(run_id: str, format: str = "markdown") -> str:
    """Get report for a completed run."""
    client = _get_client()
    result = client.get_report(run_id, format)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps({"success": True, **result})


def list_veriflow_runs(project_id: str = "") -> str:
    """List Veriflow runs."""
    client = _get_client()
    runs = client.list_runs(project_id if project_id else None)

    if runs and "error" in runs[0]:
        return json.dumps({"success": False, "error": runs[0]["error"]})

    return json.dumps({"success": True, "runs": runs})


def wait_for_veriflow_run(run_id: str, timeout: int = 300, poll_interval: int = 10) -> str:
    """Wait for a run to complete."""
    client = _get_client()
    start = time.time()

    while time.time() - start < timeout:
        result = client.get_run_status(run_id)
        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]})

        status = result.get("status", "unknown")
        if status in ("completed", "failed", "cancelled"):
            return json.dumps({"success": True, **result})

        time.sleep(poll_interval)

    return json.dumps({"success": False, "error": "Timeout waiting for run"})


# CLI command handlers
def cmd_run(args: List[str]) -> str:
    """Handle /veriflow run command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/veriflow run")
    parser.add_argument("--repo", "-r")
    parser.add_argument("--name", "-n")
    parser.add_argument("--feature", "-f")
    parser.add_argument("--mode", "-m", choices=["smoke", "regression", "full"], default="regression")
    parsed = parser.parse_args(args)

    return run_veriflow_qa(
        repo_url=parsed.repo or "",
        name=parsed.name or "",
        feature=parsed.feature or "",
        mode=parsed.mode,
    )


def cmd_status(args: List[str]) -> str:
    """Handle /veriflow status command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/veriflow status")
    parser.add_argument("run_id")
    parsed = parser.parse_args(args)

    return get_veriflow_status(parsed.run_id)


def cmd_report(args: List[str]) -> str:
    """Handle /veriflow report command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/veriflow report")
    parser.add_argument("run_id")
    parser.add_argument("--format", choices=["html", "markdown", "json"], default="markdown")
    parsed = parser.parse_args(args)

    return get_veriflow_report(parsed.run_id, parsed.format)


def cmd_wait(args: List[str]) -> str:
    """Handle /veriflow wait command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/veriflow wait")
    parser.add_argument("run_id")
    parser.add_argument("--timeout", type=int, default=300)
    parsed = parser.parse_args(args)

    return wait_for_veriflow_run(parsed.run_id, parsed.timeout)


def cmd_list(args: List[str]) -> str:
    """Handle /veriflow list command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/veriflow list")
    parser.add_argument("--project", "-p")
    parsed = parser.parse_args(args)

    return list_veriflow_runs(parsed.project or "")


def cmd_config(args: List[str]) -> str:
    """Handle /veriflow config command."""
    config = _load_config()
    # Mask API key
    if config.get("veriflow_api_key"):
        config["veriflow_api_key"] = "***"
    return json.dumps(config, indent=2)