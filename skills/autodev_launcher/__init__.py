"""
AutoDev Launcher Skill for Hermes.

Launches AutoDev Office projects via REST API — turns requirements into
full SDLC: plan → design → code → QA → deploy → handover.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from hermes_constants import get_hermes_home


class AutoDevClient:
    """Client for AutoDev Office API."""

    def __init__(self, base_url: str = "http://localhost:4000", dashboard_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip("/")
        self.dashboard_url = dashboard_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)

    def health_check(self) -> dict[str, Any]:
        """Check if AutoDev API is healthy."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/health")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_project(
        self,
        brief: str,
        email: str = "",
        mode: str = "mock",
        budget: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a new AutoDev project."""
        payload = {"brief": brief, "mode": mode}
        if email:
            payload["email"] = email
        if budget:
            payload["budget_usd"] = budget

        try:
            resp = self.client.post(
                f"{self.base_url}/api/v1/projects",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Get project details."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/projects/{project_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_project_dag(self, project_id: str) -> dict[str, Any]:
        """Get project DAG (task graph)."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/projects/{project_id}/dag")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_project_logs(self, project_id: str, stage: str = "") -> str:
        """Get project logs."""
        try:
            params = {}
            if stage:
                params["stage"] = stage
            resp = self.client.get(
                f"{self.base_url}/api/v1/projects/{project_id}/logs",
                params=params,
                timeout=120.0,
            )
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            return f"Error fetching logs: {e}"

    def get_project_artifacts(self, project_id: str) -> list[dict[str, Any]]:
        """Get project artifacts."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/projects/{project_id}/artifacts")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return [{"error": str(e)}]

    def get_staging_url(self, project_id: str) -> dict[str, Any]:
        """Get staging preview URL for a project."""
        try:
            resp = self.client.get(f"{self.base_url}/api/v1/projects/{project_id}/url")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def approve_gate(self, project_id: str, gate: str) -> dict[str, Any]:
        """Approve a gate (proposal or release)."""
        try:
            resp = self.client.post(
                f"{self.base_url}/api/v1/projects/{project_id}/gates/{gate}/approve",
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def reject_gate(self, project_id: str, gate: str, reason: str) -> dict[str, Any]:
        """Reject a gate."""
        try:
            resp = self.client.post(
                f"{self.base_url}/api/v1/projects/{project_id}/gates/{gate}/reject",
                json={"reason": reason},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def list_projects(self, status: str = "") -> list[dict[str, Any]]:
        """List projects."""
        try:
            params = {}
            if status:
                params["status"] = status
            resp = self.client.get(f"{self.base_url}/api/v1/projects", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return [{"error": str(e)}]


def _load_config() -> dict[str, Any]:
    """Load skill config from Hermes config.yaml via the canonical (ruamel-backed) loader."""
    try:
        from hermes_cli.config import load_config

        config = load_config()
    except Exception:
        return {}
    if not isinstance(config, dict):
        return {}
    return config.get("skills", {}).get("config", {}).get("autodev_launcher", {})


def _get_client() -> AutoDevClient:
    """Get configured AutoDev client."""
    config = _load_config()
    base_url = config.get("autodev_base_url", "http://localhost:4000")
    dashboard_url = config.get("autodev_dashboard_url", "http://localhost:3000")
    return AutoDevClient(base_url, dashboard_url)


# Main skill functions
def create_autodev_project(
    brief: str,
    email: str = "",
    mode: str = "mock",
    budget: Optional[int] = None,
) -> str:
    """
    Create an AutoDev Office project.

    Args:
        brief: Project requirement description
        email: Notification email
        mode: mock | gated | proposal_only
        budget: Budget in USD (for gated mode)

    Returns:
        JSON string with project_id and status
    """
    config = _load_config()
    default_email = config.get("default_email", "")

    client = _get_client()

    if not email:
        email = default_email

    result = client.create_project(brief, email, mode, budget)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps(
        {
            "success": True,
            "project_id": result.get("id"),
            "status": result.get("status", "created"),
            "message": f"AutoDev project created: {brief[:60]}...",
            "dashboard_url": f"{client.dashboard_url}/projects/{result.get('id')}",
        }
    )


def get_autodev_status(project_id: str) -> str:
    """Get project status and DAG."""
    client = _get_client()
    project = client.get_project(project_id)

    if "error" in project:
        return json.dumps({"success": False, "error": project["error"]})

    dag = client.get_project_dag(project_id)

    return json.dumps(
        {
            "success": True,
            "project": project,
            "dag": dag if "error" not in dag else None,
        }
    )


def get_autodev_logs(project_id: str, stage: str = "") -> str:
    """Get project logs."""
    client = _get_client()
    logs = client.get_project_logs(project_id, stage)
    return json.dumps({"success": True, "logs": logs})


def get_autodev_artifacts(project_id: str) -> str:
    """Get project artifacts."""
    client = _get_client()
    artifacts = client.get_project_artifacts(project_id)

    if artifacts and "error" in artifacts[0]:
        return json.dumps({"success": False, "error": artifacts[0]["error"]})

    return json.dumps({"success": True, "artifacts": artifacts})


def get_autodev_url(project_id: str) -> str:
    """Get staging preview URL."""
    client = _get_client()
    result = client.get_staging_url(project_id)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps({"success": True, **result})


def approve_autodev_gate(project_id: str, gate: str) -> str:
    """Approve a gate."""
    client = _get_client()
    result = client.approve_gate(project_id, gate)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps({"success": True, **result})


def reject_autodev_gate(project_id: str, gate: str, reason: str) -> str:
    """Reject a gate."""
    client = _get_client()
    result = client.reject_gate(project_id, gate, reason)

    if "error" in result:
        return json.dumps({"success": False, "error": result["error"]})

    return json.dumps({"success": True, **result})


def list_autodev_projects(status: str = "") -> str:
    """List AutoDev projects."""
    client = _get_client()
    projects = client.list_projects(status if status else None)

    if projects and "error" in projects[0]:
        return json.dumps({"success": False, "error": projects[0]["error"]})

    return json.dumps({"success": True, "projects": projects})


# CLI command handlers
def cmd_create(args: list[str]) -> str:
    """Handle /autodev create command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev create")
    parser.add_argument("brief", nargs=argparse.REMAINDER)
    parser.add_argument("--email", "-e")
    parser.add_argument("--mode", "-m", choices=["mock", "gated", "proposal_only"], default="mock")
    parser.add_argument("--budget", "-b", type=int)

    # Parse manually since brief is the rest
    brief_parts = []
    email = ""
    mode = "mock"
    budget = None

    i = 0
    while i < len(args):
        if args[i] == "--email" or args[i] == "-e":
            email = args[i + 1]
            i += 2
        elif args[i] == "--mode" or args[i] == "-m":
            mode = args[i + 1]
            i += 2
        elif args[i] == "--budget" or args[i] == "-b":
            budget = int(args[i + 1])
            i += 2
        else:
            brief_parts.append(args[i])
            i += 1

    brief = " ".join(brief_parts)
    if not brief:
        return "Usage: /autodev create \"requirement text\" [--email EMAIL] [--mode mock|gated] [--budget N]"

    return create_autodev_project(brief, email, mode, budget)


def cmd_status(args: list[str]) -> str:
    """Handle /autodev status command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev status")
    parser.add_argument("project_id")
    parsed = parser.parse_args(args)

    return get_autodev_status(parsed.project_id)


def cmd_logs(args: list[str]) -> str:
    """Handle /autodev logs command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev logs")
    parser.add_argument("project_id")
    parser.add_argument("--stage", "-s")
    parsed = parser.parse_args(args)

    return get_autodev_logs(parsed.project_id, parsed.stage or "")


def cmd_artifacts(args: list[str]) -> str:
    """Handle /autodev artifacts command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev artifacts")
    parser.add_argument("project_id")
    parsed = parser.parse_args(args)

    return get_autodev_artifacts(parsed.project_id)


def cmd_url(args: list[str]) -> str:
    """Handle /autodev url command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev url")
    parser.add_argument("project_id")
    parsed = parser.parse_args(args)

    return get_autodev_url(parsed.project_id)


def cmd_approve(args: list[str]) -> str:
    """Handle /autodev approve command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev approve")
    parser.add_argument("project_id")
    parser.add_argument("--gate", "-g", choices=["proposal", "release"], required=True)
    parsed = parser.parse_args(args)

    return approve_autodev_gate(parsed.project_id, parsed.gate)


def cmd_reject(args: list[str]) -> str:
    """Handle /autodev reject command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev reject")
    parser.add_argument("project_id")
    parser.add_argument("--gate", "-g", choices=["proposal", "release"], required=True)
    parser.add_argument("--reason", "-r", required=True)
    parsed = parser.parse_args(args)

    return reject_autodev_gate(parsed.project_id, parsed.gate, parsed.reason)


def cmd_list(args: list[str]) -> str:
    """Handle /autodev list command."""
    import argparse

    parser = argparse.ArgumentParser(prog="/autodev list")
    parser.add_argument("--status", "-s")
    parsed = parser.parse_args(args)

    return list_autodev_projects(parsed.status or "")