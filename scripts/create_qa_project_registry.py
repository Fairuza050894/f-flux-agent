from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

PROJECTS_ROOT = (
    ROOT
    / "skills"
    / "qa_automation"
    / "projects"
)

REGISTRY_PATH = (
    PROJECTS_ROOT
    / "project_registry.json"
)


def write_json_if_missing(
    path: Path,
    payload: dict,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if path.exists():
        print(
            f"Preserved existing file: {path}"
        )
        return

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Created: {path}")


def load_json(path: Path, default):
    if not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


# ============================================================
# Mobospace
# ============================================================

mobospace_root = (
    PROJECTS_ROOT
    / "mobospace"
)

write_json_if_missing(
    mobospace_root / "project.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "name": "Mobospace",
        "description": (
            "Logistics and shipment "
            "monitoring platform"
        ),
        "status": "active",
        "default_environment": "sandbox",
        "supported_test_types": [
            "ui",
            "api",
            "regression",
            "e2e",
        ],
        "runner_adapter": (
            "existing_registered_qa"
        ),
        "configuration_source": (
            "existing_checker_configuration"
        ),
        "files": {
            "environments": (
                "environments.json"
            ),
            "features": "features.json",
            "regression_suites": (
                "regression_suites.json"
            ),
            "api_collections": (
                "api_collections.json"
            ),
            "e2e_flows": "e2e_flows.json",
        },
    },
)

write_json_if_missing(
    mobospace_root / "environments.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "environments": [
            {
                "environment_id": (
                    "sandbox"
                ),
                "name": "Sandbox",
                "status": "active",
                "base_url_source": (
                    "existing_checker_configuration"
                ),
                "credential_source": (
                    "existing_checker_configuration"
                ),
            }
        ],
    },
)

write_json_if_missing(
    mobospace_root / "features.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "features": [
            {
                "feature_id": (
                    "driver-daily-meal"
                ),
                "name": (
                    "Uang Makan Driver"
                ),
                "runner_feature_name": (
                    "Uang Makan Driver"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
            {
                "feature_id": (
                    "shipment-details"
                ),
                "name": (
                    "Shipment Details"
                ),
                "runner_feature_name": (
                    "Shipment Details"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
            {
                "feature_id": "mobomap",
                "name": "MoboMap",
                "runner_feature_name": (
                    "MoboMap"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
            {
                "feature_id": (
                    "inspection-result"
                ),
                "name": (
                    "Inspection Result"
                ),
                "runner_feature_name": (
                    "Inspection Result"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
            {
                "feature_id": (
                    "notification-messages"
                ),
                "name": (
                    "Notification Messages"
                ),
                "runner_feature_name": (
                    "Notification Messages"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
            {
                "feature_id": (
                    "notification-management"
                ),
                "name": (
                    "Notification Management"
                ),
                "runner_feature_name": (
                    "Notification Management"
                ),
                "test_type": (
                    "ui_regression"
                ),
                "status": "active",
            },
        ],
    },
)

write_json_if_missing(
    mobospace_root
    / "regression_suites.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "regression_suites": [
            {
                "suite_id": (
                    "driver-operations"
                ),
                "name": (
                    "Driver Operations"
                ),
                "feature_ids": [
                    "driver-daily-meal",
                ],
                "status": "active",
            },
            {
                "suite_id": (
                    "shipment-monitoring"
                ),
                "name": (
                    "Shipment Monitoring"
                ),
                "feature_ids": [
                    "shipment-details",
                    "mobomap",
                ],
                "status": "active",
            },
            {
                "suite_id": "inspection",
                "name": "Inspection",
                "feature_ids": [
                    "inspection-result",
                ],
                "status": "active",
            },
            {
                "suite_id": "notification",
                "name": "Notification",
                "feature_ids": [
                    "notification-messages",
                    "notification-management",
                ],
                "status": "active",
            },
            {
                "suite_id": "all-features",
                "name": "All Features",
                "feature_ids": [
                    "driver-daily-meal",
                    "shipment-details",
                    "mobomap",
                    "inspection-result",
                    "notification-messages",
                    "notification-management",
                ],
                "status": "active",
            },
        ],
    },
)

write_json_if_missing(
    mobospace_root
    / "api_collections.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "api_collections": [],
    },
)

write_json_if_missing(
    mobospace_root / "e2e_flows.json",
    {
        "schema_version": "1.0",
        "project_id": "mobospace",
        "e2e_flows": [],
    },
)


# ============================================================
# Ad-hoc Testing
# ============================================================

adhoc_root = (
    PROJECTS_ROOT
    / "adhoc"
)

write_json_if_missing(
    adhoc_root / "project.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "name": "Ad-hoc Testing",
        "description": (
            "Generic UI and API testing "
            "using a custom target"
        ),
        "status": "active",
        "default_environment": "custom",
        "supported_test_types": [
            "ui",
            "api",
        ],
        "runner_adapter": (
            "generic_dashboard_runner"
        ),
        "configuration_source": (
            "runtime_input"
        ),
        "files": {
            "environments": (
                "environments.json"
            ),
            "features": "features.json",
            "regression_suites": (
                "regression_suites.json"
            ),
            "api_collections": (
                "api_collections.json"
            ),
            "e2e_flows": "e2e_flows.json",
        },
    },
)

write_json_if_missing(
    adhoc_root / "environments.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "environments": [
            {
                "environment_id": "custom",
                "name": "Custom",
                "status": "active",
                "base_url_source": (
                    "runtime_input"
                ),
                "credential_source": (
                    "runtime_input"
                ),
            }
        ],
    },
)

write_json_if_missing(
    adhoc_root / "features.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "features": [],
    },
)

write_json_if_missing(
    adhoc_root
    / "regression_suites.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "regression_suites": [],
    },
)

write_json_if_missing(
    adhoc_root
    / "api_collections.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "api_collections": [],
    },
)

write_json_if_missing(
    adhoc_root / "e2e_flows.json",
    {
        "schema_version": "1.0",
        "project_id": "adhoc",
        "e2e_flows": [],
    },
)


# ============================================================
# Project registry
# ============================================================

registry = load_json(
    REGISTRY_PATH,
    {
        "schema_version": "1.0",
        "projects": [],
    },
)

if not isinstance(registry, dict):
    registry = {
        "schema_version": "1.0",
        "projects": [],
    }

projects = registry.get("projects")

if not isinstance(projects, list):
    projects = []

required_entries = [
    {
        "project_id": "mobospace",
        "name": "Mobospace",
        "description": (
            "Logistics and shipment "
            "monitoring platform"
        ),
        "status": "active",
        "config_path": (
            "mobospace/project.json"
        ),
    },
    {
        "project_id": "adhoc",
        "name": "Ad-hoc Testing",
        "description": (
            "Generic UI and API testing "
            "using a custom target"
        ),
        "status": "active",
        "config_path": (
            "adhoc/project.json"
        ),
    },
]

existing_ids = {
    str(item.get("project_id"))
    for item in projects
    if isinstance(item, dict)
}

for entry in required_entries:
    if entry["project_id"] not in existing_ids:
        projects.append(entry)

registry["schema_version"] = "1.0"
registry["projects"] = projects

REGISTRY_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REGISTRY_PATH.write_text(
    json.dumps(
        registry,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print(f"Updated registry: {REGISTRY_PATH}")
print(f"Project count: {len(projects)}")
